"""Ask Agent side panel widget for asking questions about ongoing conversation."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from rich.markup import escape
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Input, Static

from openhands_cli.theme import OPENHANDS_THEME
from openhands_cli.tui.panels.ask_agent_panel_style import ASK_AGENT_PANEL_STYLE


if TYPE_CHECKING:
    from openhands_cli.tui.textual_app import OpenHandsApp


logger = logging.getLogger(__name__)


class AskAgentPanel(Vertical):
    """Side panel widget for asking questions about the ongoing conversation.

    This panel allows users to ask questions about the conversation trajectory
    without adding them to the main conversation. Uses conversation.ask_agent()
    which is thread-safe and can be called while the conversation is running.
    """

    DEFAULT_CSS = ASK_AGENT_PANEL_STYLE

    def __init__(self, app: OpenHandsApp, **kwargs):
        """Initialize the Ask Agent panel."""
        super().__init__(**kwargs)
        self._oh_app = app
        self._is_loading = False

    def compose(self):
        """Compose the Ask Agent panel content."""
        with Horizontal(classes="ask-agent-header-row"):
            yield Static("Ask About Conversation", classes="ask-agent-header")
        yield Input(
            placeholder="Ask a question about the conversation...",
            id="ask-agent-input",
        )
        yield Button("Ask", id="ask-agent-submit-btn")
        yield Static(
            f"[{OPENHANDS_THEME.foreground}]"
            f"Ask questions about the ongoing conversation.\n"
            f"These questions are not added to the conversation."
            f"[/{OPENHANDS_THEME.foreground}]",
            id="ask-agent-output",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "ask-agent-submit-btn":
            self._submit_question()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission (Enter key)."""
        if event.input.id == "ask-agent-input":
            self._submit_question()

    def _submit_question(self) -> None:
        """Submit the question to the agent."""
        if self._is_loading:
            return

        input_widget = self.query_one("#ask-agent-input", Input)
        question = input_widget.value.strip()

        if not question:
            return

        # Clear input
        input_widget.value = ""

        # Start async task to ask the agent
        asyncio.create_task(self._ask_agent_async(question))

    async def _ask_agent_async(self, question: str) -> None:
        """Ask the agent asynchronously."""
        output_widget = self.query_one("#ask-agent-output", Static)

        # Check if conversation runner exists
        if not self._oh_app.conversation_runner:
            output_widget.update(
                f"[{OPENHANDS_THEME.error}]"
                f"No active conversation. Start a conversation first."
                f"[/{OPENHANDS_THEME.error}]"
            )
            return

        # Show loading state
        self._is_loading = True
        output_widget.update(
            f"[{OPENHANDS_THEME.warning}]"
            f"Thinking..."
            f"[/{OPENHANDS_THEME.warning}]"
        )

        try:
            # Call ask_agent in a thread to avoid blocking UI
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                self._oh_app.conversation_runner.conversation.ask_agent,
                question,
            )

            # Display the response
            escaped_question = escape(question)
            escaped_response = escape(response)
            output_widget.update(
                f"[{OPENHANDS_THEME.accent}]Q: {escaped_question}[/{OPENHANDS_THEME.accent}]\n\n"
                f"[{OPENHANDS_THEME.foreground}]{escaped_response}[/{OPENHANDS_THEME.foreground}]"
            )
        except Exception as e:
            logger.exception("Error asking agent")
            output_widget.update(
                f"[{OPENHANDS_THEME.error}]"
                f"Error: {escape(str(e))}"
                f"[/{OPENHANDS_THEME.error}]"
            )
        finally:
            self._is_loading = False
