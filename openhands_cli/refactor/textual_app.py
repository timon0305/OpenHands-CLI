"""Minimal textual app for OpenHands CLI migration.

This is the starting point for migrating from prompt_toolkit to textual.
It creates a basic app with:
- A scrollable main display (RichLog) that shows the splash screen initially
- An Input widget at the bottom for user messages
- The splash screen content scrolls off as new messages are added
"""

from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Input, RichLog
from textual_autocomplete import AutoComplete, DropdownItem, TargetState

from openhands_cli.refactor.splash import get_welcome_message
from openhands_cli.refactor.theme import OPENHANDS_THEME


class CommandAutoComplete(AutoComplete):
    """Custom AutoComplete showing descriptions after commands, completing command."""

    def get_search_string(self, target_state: TargetState) -> str:
        """Only match on the leading command token (e.g. `/help`).

        Any characters after the first space (like arguments or ` - `)
        will stop autocomplete from matching at all.
        """
        # Text up to the cursor
        raw = target_state.text[: target_state.cursor_position]

        # Ignore leading whitespace
        raw = raw.lstrip()

        # Only trigger autocomplete if we're starting with a slash-command
        if not raw.startswith("/"):
            return ""

        # If there's a space, user has started typing arguments (" /help - ...")
        # => stop matching entirely
        if " " in raw:
            return ""

        # Otherwise, use the whole token as the search string (e.g. "/he", "/help")
        return raw

    def apply_completion(self, value: str, state) -> None:  # noqa: ARG002
        """Apply completion, but only insert the command part (before the ' - ')."""
        # Extract just the command part (before the description)
        if " - " in value:
            command_only = value.split(" - ")[0]
        else:
            command_only = value

        # Apply the command-only completion to the target input
        if self.target:
            self.target.value = ""
            self.target.insert_text_at_cursor(command_only)


# Available commands with descriptions after the command
COMMANDS = [
    DropdownItem(main="/help - Display available commands"),
    DropdownItem(main="/exit - Exit the application"),
]


class OpenHandsApp(App):
    """A minimal textual app for OpenHands CLI with scrollable main display."""

    def __init__(self, **kwargs):
        """Initialize the app with custom OpenHands theme."""
        super().__init__(**kwargs)

        # Register the custom theme
        self.register_theme(OPENHANDS_THEME)

        # Set the theme as active
        self.theme = "openhands"

    CSS = """
    Screen {
        layout: vertical;
        background: $background;
    }

    #main_display {
        height: 1fr;
        margin: 1 1 0 1;
        overflow-y: scroll;
        background: $background;
        color: $foreground;
    }

    #input_area {
        height: 8;
        dock: bottom;
        background: $background;
        padding: 1;
        margin-bottom: 1;
    }

    #user_input {
        width: 100%;
        height: 3;
        background: $background;
        color: $foreground;
        border: solid $secondary;
    }

    #user_input:focus {
        border: solid $primary;
        background: $background;
    }

    /* Style the cursor to use primary color */
    Input .input--cursor {
        background: $primary;
        color: $background;
    }
    """

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        # Main scrollable display
        main_display = RichLog(id="main_display", highlight=False, markup=True)
        main_display.can_focus = False
        yield main_display

        # Input area - docked to bottom
        with Container(id="input_area"):
            text_input = Input(
                placeholder=(
                    "Type your message… (tip: press \\ + Enter to insert a newline)"
                ),
                id="user_input",
            )
            yield text_input

            # Add autocomplete for the input
            yield CommandAutoComplete(text_input, candidates=COMMANDS)

    def on_mount(self) -> None:
        """Called when app starts."""
        # Add the splash screen content to the main display
        main_display = self.query_one("#main_display", RichLog)
        splash_content = get_welcome_message(theme=OPENHANDS_THEME)
        main_display.write(splash_content)

        # Focus the input widget
        self.query_one("#user_input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle when user submits input."""
        user_message = event.value.strip()
        if user_message:
            # Add the user message to the main display
            main_display = self.query_one("#main_display", RichLog)
            main_display.write(f"\n> {user_message}")

            # Handle commands
            if user_message.startswith("/"):
                self._handle_command(user_message)
            else:
                # Handle regular messages (placeholder for now)
                main_display.write("Regular message handling not implemented yet.")

            # Clear the input
            event.input.value = ""

    def _handle_command(self, command: str) -> None:
        """Handle command execution."""
        main_display = self.query_one("#main_display", RichLog)

        if command == "/help":
            self._show_help()
        elif command == "/exit":
            self._handle_exit()
        else:
            main_display.write(f"Unknown command: {command}")

    def _show_help(self) -> None:
        """Display help information."""
        main_display = self.query_one("#main_display", RichLog)

        help_text = """
[bold yellow]OpenHands CLI Help[/bold yellow]
[dim]Available commands:[/dim]

  [white]/help[/white] - Display available commands
  [white]/exit[/white] - Exit the application

[dim]Tips:[/dim]
  • Type / and press Tab to see command suggestions
  • Use arrow keys to navigate through suggestions
  • Press Enter to select a command
"""
        main_display.write(help_text)

    def _handle_exit(self) -> None:
        """Handle exit command with confirmation."""
        # For now, just show a message and exit
        # TODO: Add proper confirmation dialog
        main_display = self.query_one("#main_display", RichLog)
        main_display.write("\n[yellow]Goodbye! 👋[/yellow]")
        self.exit()


def main():
    """Run the textual app."""
    app = OpenHandsApp()
    app.run()


if __name__ == "__main__":
    main()
