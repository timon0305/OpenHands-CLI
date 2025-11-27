"""
Textual-compatible visualizer for OpenHands conversation events.
This replaces the Rich-based CLIVisualizer with a Textual-compatible version.
"""

import re
import threading
from typing import TYPE_CHECKING

from rich.text import Text
from textual.widgets import Collapsible, Static

from openhands.sdk.conversation.visualizer.base import ConversationVisualizerBase
from openhands.sdk.event import (
    ActionEvent,
    AgentErrorEvent,
    MessageEvent,
    ObservationEvent,
    PauseEvent,
    SystemPromptEvent,
    UserRejectObservation,
)
from openhands.sdk.event.base import Event
from openhands.sdk.event.condenser import Condensation


if TYPE_CHECKING:
    from textual.containers import VerticalScroll

    from openhands_cli.refactor.textual_app import OpenHandsApp


# Color scheme matching the original visualizer
_OBSERVATION_COLOR = "yellow"
_MESSAGE_USER_COLOR = "gold3"
_PAUSE_COLOR = "bright_yellow"
_SYSTEM_COLOR = "magenta"
_THOUGHT_COLOR = "bright_black"
_ERROR_COLOR = "red"
_ACTION_COLOR = "blue"
_MESSAGE_ASSISTANT_COLOR = _ACTION_COLOR

DEFAULT_HIGHLIGHT_REGEX = {
    r"^Reasoning:": f"bold {_THOUGHT_COLOR}",
    r"^Thought:": f"bold {_THOUGHT_COLOR}",
    r"^Action:": f"bold {_ACTION_COLOR}",
    r"^Arguments:": f"bold {_ACTION_COLOR}",
    r"^Tool:": f"bold {_OBSERVATION_COLOR}",
    r"^Result:": f"bold {_OBSERVATION_COLOR}",
    r"^Rejection Reason:": f"bold {_ERROR_COLOR}",
    # Markdown-style
    r"\*\*(.*?)\*\*": "bold",
    r"\*(.*?)\*": "italic",
}


class TextualVisualizer(ConversationVisualizerBase):
    """Handles visualization of conversation events for Textual apps.

    This visualizer creates Collapsible widgets and adds them to a VerticalScroll container.
    """

    def __init__(
        self,
        container: "VerticalScroll",
        app: "OpenHandsApp",
        highlight_regex: dict[str, str] | None = DEFAULT_HIGHLIGHT_REGEX,
        skip_user_messages: bool = False,
    ):
        """Initialize the visualizer.

        Args:
            container: The Textual VerticalScroll container to add widgets to
            app: The Textual app instance for thread-safe UI updates
            highlight_regex: Dictionary mapping regex patterns to Rich color styles
            skip_user_messages: If True, skip displaying user messages
        """
        super().__init__()
        self._container = container
        self._app = app
        self._skip_user_messages = skip_user_messages
        self._highlight_patterns = highlight_regex or {}
        # Store the main thread ID for thread safety checks
        self._main_thread_id = threading.get_ident()

    def on_event(self, event: Event) -> None:
        """Main event handler that creates Collapsible widgets for events."""
        collapsible_widget = self._create_event_collapsible(event)
        if collapsible_widget:
            # Check if we're in the main thread or a background thread
            current_thread_id = threading.get_ident()
            if current_thread_id == self._main_thread_id:
                # We're in the main thread, update UI directly
                self._add_widget_to_ui(collapsible_widget)
            else:
                # We're in a background thread, use call_from_thread
                self._app.call_from_thread(self._add_widget_to_ui, collapsible_widget)

    def _add_widget_to_ui(self, widget: Collapsible) -> None:
        """Add a widget to the UI (must be called from main thread)."""
        self._container.mount(widget)

    def _apply_highlighting(self, text: Text) -> Text:
        """Apply regex-based highlighting to text content."""
        if not self._highlight_patterns:
            return text

        # Ensure we have a Text object
        if not isinstance(text, Text):
            text = Text(str(text))

        # Create a copy to avoid modifying the original
        highlighted = text.copy()

        # Apply each pattern using Rich's built-in highlight_regex method
        for pattern, style in self._highlight_patterns.items():
            pattern_compiled = re.compile(pattern, re.MULTILINE)
            highlighted.highlight_regex(pattern_compiled, style)

        return highlighted

    def _create_event_collapsible(self, event: Event) -> Collapsible | None:
        """Create a Collapsible widget for the event with appropriate styling."""
        # Use the event's visualize property for content
        content = event.visualize

        if not content.plain.strip():
            return None

        # Apply highlighting if configured
        if self._highlight_patterns:
            content = self._apply_highlighting(content)

        # Don't emit system prompt in CLI
        if isinstance(event, SystemPromptEvent):
            return None
        elif isinstance(event, ActionEvent):
            # Check if action is None (non-executable)
            if event.action is None:
                title = "Agent Action (Not Executed)"
            else:
                title = "Agent Action"
            
            # Create content widget with metrics subtitle if available
            content_widget = Static(content)
            metrics = self._format_metrics_subtitle()
            if metrics:
                content_widget = Static(f"{content}\n\n{metrics}")
            
            return Collapsible(
                content_widget,
                title=title,
                collapsed=True,  # Start collapsed by default
            )
        elif isinstance(event, ObservationEvent):
            title = "Observation"
            content_widget = Static(content)
            return Collapsible(
                content_widget,
                title=title,
                collapsed=True,  # Start collapsed for observations
            )
        elif isinstance(event, UserRejectObservation):
            title = "User Rejected Action"
            content_widget = Static(content)
            return Collapsible(
                content_widget,
                title=title,
                collapsed=True,  # Start collapsed by default
            )
        elif isinstance(event, MessageEvent):
            if (
                self._skip_user_messages
                and event.llm_message
                and event.llm_message.role == "user"
            ):
                return None
            assert event.llm_message is not None
            
            if event.llm_message.role == "user":
                title = "User Message to Agent"
            else:
                title = "Message from Agent"
            
            # Create content widget with metrics if available
            content_widget = Static(content)
            metrics = self._format_metrics_subtitle()
            if metrics and event.llm_message.role == "assistant":
                content_widget = Static(f"{content}\n\n{metrics}")
            
            return Collapsible(
                content_widget,
                title=title,
                collapsed=True,  # Start collapsed by default
            )
        elif isinstance(event, AgentErrorEvent):
            title = "Agent Error"
            content_widget = Static(content)
            metrics = self._format_metrics_subtitle()
            if metrics:
                content_widget = Static(f"{content}\n\n{metrics}")
            
            return Collapsible(
                content_widget,
                title=title,
                collapsed=True,  # Start collapsed by default
            )
        elif isinstance(event, PauseEvent):
            title = "User Paused"
            content_widget = Static(content)
            return Collapsible(
                content_widget,
                title=title,
                collapsed=True,  # Start collapsed for pauses
            )
        elif isinstance(event, Condensation):
            title = "Condensation"
            content_widget = Static(content)
            metrics = self._format_metrics_subtitle()
            if metrics:
                content_widget = Static(f"{content}\n\n{metrics}")
            
            return Collapsible(
                content_widget,
                title=title,
                collapsed=True,  # Start collapsed for condensations
            )
        else:
            # Fallback for unknown event types
            title = f"UNKNOWN Event: {event.__class__.__name__}"
            content_widget = Static(f"{content}\n\nSource: {event.source}")
            return Collapsible(
                content_widget,
                title=title,
                collapsed=True,  # Start collapsed for unknown events
            )

    def _format_metrics_subtitle(self) -> str | None:
        """Format LLM metrics as a visually appealing subtitle string."""
        stats = self.conversation_stats
        if not stats:
            return None

        combined_metrics = stats.get_combined_metrics()
        if not combined_metrics or not combined_metrics.accumulated_token_usage:
            return None

        usage = combined_metrics.accumulated_token_usage
        cost = combined_metrics.accumulated_cost or 0.0

        # helper: 1234 -> "1.2K", 1200000 -> "1.2M"
        def abbr(n: int | float) -> str:
            n = int(n or 0)
            if n >= 1_000_000_000:
                val, suffix = n / 1_000_000_000, "B"
            elif n >= 1_000_000:
                val, suffix = n / 1_000_000, "M"
            elif n >= 1_000:
                val, suffix = n / 1_000, "K"
            else:
                return str(n)
            return f"{val:.2f}".rstrip("0").rstrip(".") + suffix

        input_tokens = abbr(usage.prompt_tokens or 0)
        output_tokens = abbr(usage.completion_tokens or 0)

        # Cache hit rate (prompt + cache)
        prompt = usage.prompt_tokens or 0
        cache_read = usage.cache_read_tokens or 0
        cache_rate = f"{(cache_read / prompt * 100):.2f}%" if prompt > 0 else "N/A"
        reasoning_tokens = usage.reasoning_tokens or 0

        # Cost
        cost_str = f"{cost:.4f}" if cost > 0 else "0.00"

        # Build with fixed color scheme
        parts: list[str] = []
        parts.append(f"[cyan]↑ input {input_tokens}[/cyan]")
        parts.append(f"[magenta]cache hit {cache_rate}[/magenta]")
        if reasoning_tokens > 0:
            parts.append(f"[yellow] reasoning {abbr(reasoning_tokens)}[/yellow]")
        parts.append(f"[blue]↓ output {output_tokens}[/blue]")
        parts.append(f"[green]$ {cost_str}[/green]")

        return "Tokens: " + " • ".join(parts)
