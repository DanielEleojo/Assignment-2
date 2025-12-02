from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from .chatroom import ChatStore
from .config import get_settings
from .guardrails import run_guardrails
from .llm_client import LLMResponse, interpret_meme
from .rag import build_cheat_context
from .telemetry import TelemetryRecord, log_record

cli = typer.Typer(add_completion=False, help="Meme interpreter CLI")
chat_cli = typer.Typer(help="Manage the local chatroom")


def _validate_inputs(conversation: str, caption: Optional[str]) -> None:
    settings = get_settings()
    guard = run_guardrails(conversation, caption or "", max_chars=settings.max_input_chars)
    if not guard.allowed:
        typer.echo(f"Guardrail triggered: {guard.reason}")
        raise typer.Exit(code=1)


@cli.command()
def interpret(
    conversation: Optional[str] = typer.Option(
        None, help="Conversation context where the meme was shared."
    ),
    chat_id: Optional[int] = typer.Option(
        None, min=1, help="Use a locally stored chat thread as context."
    ),
    meme_image: Optional[Path] = typer.Option(
        None, exists=True, file_okay=True, dir_okay=False, help="Path to the meme image."
    ),
    caption: Optional[str] = typer.Option(None, help="Optional textual description of the meme."),
    show_chat: bool = typer.Option(False, help="Print the chat context before interpreting."),
    show_cheat_sheet: bool = typer.Option(
        False, help="Print the retrieved cheat-sheet insights before calling the LLM."
    ),
) -> None:
    selected_sources = [bool(conversation), bool(chat_id)]
    if sum(selected_sources) == 0:
        typer.echo("Provide --conversation or --chat-id for context.")
        raise typer.Exit(code=1)
    if sum(selected_sources) > 1:
        typer.echo("Choose exactly one source of conversation context.")
        raise typer.Exit(code=1)

    convo_text = conversation or ""
    pathway = "none"

    if chat_id is not None:
        store = ChatStore()
        try:
            thread = store.get_thread(chat_id)
        except ValueError as exc:
            typer.echo(str(exc))
            raise typer.Exit(code=1)
        convo_text = thread.as_prompt_context()
        if show_chat:
            typer.echo("\n=== Chatroom Thread ===\n")
            typer.echo(thread.pretty())

    if not convo_text.strip():
        typer.echo("Conversation context is empty. Provide more detail.")
        raise typer.Exit(code=1)

    _validate_inputs(convo_text, caption)

    cheat_context, matches = build_cheat_context(convo_text, caption)
    if cheat_context:
        pathway = "rag"
    if show_cheat_sheet and matches:
        typer.echo("\n=== Cheat Sheet Insights ===\n")
        for match in matches:
            typer.echo(f"- {match.entry.title}: {match.entry.guidance} (score {match.score:.2f})")

    try:
        llm_response: LLMResponse = interpret_meme(convo_text, cheat_context, caption, meme_image)
    except Exception as exc:  # noqa: BLE001
        typer.echo(f"LLM call failed: {exc}")
        raise typer.Exit(code=1)

    typer.echo("\n=== Meme Interpretation ===\n")
    typer.echo(llm_response.text)

    log_record(
        TelemetryRecord(
            pathway=pathway,
            latency_ms=llm_response.latency_ms,
            prompt_tokens=llm_response.prompt_tokens,
            response_tokens=llm_response.response_tokens,
            cost_usd=None,
        )
    )


@chat_cli.command("new")
def chat_new(
    title: str = typer.Argument(..., help="Title for the new chat thread."),
    description: str = typer.Option("", "--description", "-d", help="Short description."),
) -> None:
    store = ChatStore()
    thread = store.create_thread(title=title, description=description)
    typer.echo(f"Created chat #{thread.chat_id}: {thread.title}")


@chat_cli.command("list")
def chat_list() -> None:
    store = ChatStore()
    threads = store.list_threads()
    if not threads:
        typer.echo("No chats yet. Use `chat new` to create one.")
        return
    for thread in threads:
        typer.echo(f"#{thread.chat_id} — {thread.title} ({len(thread.messages)} messages)")


@chat_cli.command("post")
def chat_post(
    chat_id: int = typer.Argument(..., help="Chat ID to post into."),
    author: str = typer.Option("anon", "--author", "-a", help="Display name for the message."),
    message: str = typer.Argument(..., help="Message text."),
) -> None:
    store = ChatStore()
    try:
        store.add_message(chat_id, author, message)
    except ValueError as exc:
        typer.echo(str(exc))
        raise typer.Exit(code=1)
    typer.echo("Message recorded.")


@chat_cli.command("show")
def chat_show(chat_id: int = typer.Argument(..., help="Chat ID to display.")) -> None:
    store = ChatStore()
    try:
        thread = store.get_thread(chat_id)
    except ValueError as exc:
        typer.echo(str(exc))
        raise typer.Exit(code=1)
    typer.echo(thread.pretty())


cli.add_typer(chat_cli, name="chat")


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
