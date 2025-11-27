"""RichLog visualizer for textual UI integration.

This module provides a custom visualizer that emits events to a RichLog display
instead of printing to console, allowing integration with textual UI components.
"""

from typing import Any, Callable

from openhands.sdk.conversation.visualizer.base import ConversationVisualizerBase
from openhands.sdk.event.base import Event
from rich.console import Console
from rich.text import Text


class RichLogVisualizer(ConversationVisualizerBase):
    """Custom visualizer that emits events to a RichLog display.
    
    This visualizer is designed to work with textual's RichLog widget,
    allowing conversation events to be displayed in the UI instead of
    being printed to the console.
    """

    def __init__(
        self,
        write_callback: Callable[[Any], None],
        highlight_regex: dict[str, str] | None = None,
        skip_user_messages: bool = False,
    ):
        """Initialize the RichLog visualizer.

        Args:
            write_callback: Function to call to write content to the RichLog.
                           Should accept any content that RichLog.write() accepts.
            highlight_regex: Dictionary mapping regex patterns to Rich color styles
                           for highlighting keywords in the visualizer.
                           For example: {"Reasoning:": "bold blue",
                           "Thought:": "bold green"}
            skip_user_messages: If True, skip displaying user messages. Useful for
                              scenarios where user input is not relevant to show.
        """
        super().__init__()
        self._write_callback = write_callback
        self._skip_user_messages = skip_user_messages
        
        # Set up default highlighting patterns if none provided
        self._highlight_regex = highlight_regex or {
            r'^Reasoning:': 'bold bright_black',
            r'^Thought:': 'bold bright_black', 
            r'^Action:': 'bold blue',
            r'^Arguments:': 'bold blue',
            r'^Tool:': 'bold yellow',
            r'^Result:': 'bold yellow',
            r'^Rejection Reason:': 'bold red',
            r'\*\*(.*?)\*\*': 'bold',
            r'\*(.*?)\*': 'italic',
        }
        
        # Create a console for Rich formatting (but don't use it for output)
        self._console = Console(file=None, width=120)

    def on_event(self, event: Event) -> None:
        """Handle conversation events by writing them to the RichLog.

        Args:
            event: The conversation event to visualize
        """
        # Import here to avoid circular imports
        from openhands.sdk.conversation.visualizer.default import EVENT_VISUALIZATION_CONFIG
        from openhands.sdk.event import MessageEvent
        
        # Get the visualization config for this event type
        event_type = type(event)
        if event_type not in EVENT_VISUALIZATION_CONFIG:
            return
            
        config = EVENT_VISUALIZATION_CONFIG[event_type]
        
        # Skip if configured to skip
        if config.skip:
            return
            
        # Skip user messages if configured to do so
        if (self._skip_user_messages and 
            isinstance(event, MessageEvent) and 
            event.source == "user"):
            return
            
        # Format the event content
        try:
            # Use the default visualization config to format the event
            formatted_content = self._format_event(event, config)
            if formatted_content:
                self._write_callback(formatted_content)
        except Exception as e:
            # Fallback to basic string representation if formatting fails
            self._write_callback(f"Event: {event}")

    def _format_event(self, event: Event, config: Any) -> str | Text | None:
        """Format an event for display.
        
        Args:
            event: The event to format
            config: The visualization configuration for this event type
            
        Returns:
            Formatted content suitable for RichLog.write(), or None if nothing to display
        """
        # Import here to avoid circular imports
        from openhands.sdk.event import MessageEvent, AgentStateEvent
        
        if isinstance(event, MessageEvent):
            return self._format_message_event(event)
        elif isinstance(event, AgentStateEvent):
            return self._format_agent_state_event(event)
        else:
            # For other event types, use a generic format
            return self._format_generic_event(event)

    def _format_message_event(self, event: "MessageEvent") -> str:
        """Format a message event.
        
        Args:
            event: The message event to format
            
        Returns:
            Formatted message string
        """
        source_prefix = {
            "user": "👤 User",
            "agent": "🤖 Agent", 
            "system": "⚙️ System"
        }.get(event.source, f"📝 {event.source.title()}")
        
        # Apply highlighting to the content
        content = self._apply_highlighting(event.content)
        
        return f"\n{source_prefix}: {content}"

    def _format_agent_state_event(self, event: "AgentStateEvent") -> str:
        """Format an agent state event.
        
        Args:
            event: The agent state event to format
            
        Returns:
            Formatted state string
        """
        state_emoji = {
            "init": "🔄",
            "running": "⚡", 
            "awaiting_user_input": "⏳",
            "finished": "✅",
            "error": "❌",
            "paused": "⏸️"
        }.get(event.state, "📊")
        
        return f"\n{state_emoji} Agent State: {event.state}"

    def _format_generic_event(self, event: Event) -> str:
        """Format a generic event.
        
        Args:
            event: The event to format
            
        Returns:
            Formatted event string
        """
        event_name = type(event).__name__.replace("Event", "")
        return f"\n📋 {event_name}: {str(event)}"

    def _apply_highlighting(self, text: str) -> str:
        """Apply regex-based highlighting to text.
        
        Args:
            text: The text to highlight
            
        Returns:
            Text with highlighting applied
        """
        import re
        
        highlighted = text
        for pattern, style in self._highlight_regex.items():
            # For now, we'll just return the text as-is since RichLog
            # handles Rich markup. In a more advanced implementation,
            # we could return Rich Text objects with proper styling.
            pass
            
        return highlighted