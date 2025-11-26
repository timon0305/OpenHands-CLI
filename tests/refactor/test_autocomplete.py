"""Tests for autocomplete functionality and command handling."""

from unittest import mock

import pytest
from textual.widgets import Input, RichLog
from textual_autocomplete import AutoComplete, TargetState

from openhands_cli.refactor.autocomplete import CommandAutoComplete
from openhands_cli.refactor.commands import COMMANDS, show_help
from openhands_cli.refactor.textual_app import OpenHandsApp


class TestCommandsAndAutocomplete:
    """Tests for command handling and autocomplete functionality."""

    def test_commands_list_exists(self):
        """Test that COMMANDS list is properly defined."""
        assert isinstance(COMMANDS, list)
        assert len(COMMANDS) > 0

        # Check that all commands are properly formatted
        command_names = [str(cmd.main) for cmd in COMMANDS]
        assert "/help - Display available commands" in command_names
        assert "/exit - Exit the application" in command_names

    async def test_autocomplete_widget_exists(self):
        """Test that CommandAutoComplete widget is created."""
        from openhands_cli.refactor.textual_app import get_welcome_message

        with mock.patch.object(get_welcome_message, "__call__", return_value="test"):
            app = OpenHandsApp()
            async with app.run_test() as pilot:
                # Check that CommandAutoComplete widget exists
                autocomplete = pilot.app.query_one(CommandAutoComplete)
                assert isinstance(autocomplete, CommandAutoComplete)
                assert isinstance(
                    autocomplete, AutoComplete
                )  # Should also be an AutoComplete

    def test_handle_command_help(self):
        """Test that /help command displays help information."""
        app = OpenHandsApp()

        # Mock the query_one method
        mock_richlog = mock.MagicMock(spec=RichLog)
        app.query_one = mock.MagicMock(return_value=mock_richlog)

        # Call the command handler
        app._handle_command("/help")

        # Check that help text was written
        mock_richlog.write.assert_called_once()
        help_text = mock_richlog.write.call_args[0][0]
        assert "OpenHands CLI Help" in help_text
        assert "/help" in help_text
        assert "/exit" in help_text

    def test_handle_command_exit(self):
        """Test that /exit command exits the app."""
        app = OpenHandsApp()

        # Mock the query_one method and exit method
        mock_richlog = mock.MagicMock(spec=RichLog)
        app.query_one = mock.MagicMock(return_value=mock_richlog)
        app.exit = mock.MagicMock()

        # Call the command handler
        app._handle_command("/exit")

        # Check that goodbye message was written and app exits
        mock_richlog.write.assert_called_once()
        goodbye_text = mock_richlog.write.call_args[0][0]
        assert "Goodbye!" in goodbye_text
        app.exit.assert_called_once()

    def test_handle_command_unknown(self):
        """Test that unknown commands show error message."""
        app = OpenHandsApp()

        # Mock the query_one method
        mock_richlog = mock.MagicMock(spec=RichLog)
        app.query_one = mock.MagicMock(return_value=mock_richlog)

        # Call the command handler with unknown command
        app._handle_command("/unknown")

        # Check that error message was written
        mock_richlog.write.assert_called_once_with("Unknown command: /unknown")

    def test_on_input_submitted_handles_commands(self):
        """Test that commands are routed to command handler."""
        app = OpenHandsApp()

        # Mock the query_one method and command handler
        mock_richlog = mock.MagicMock(spec=RichLog)
        app.query_one = mock.MagicMock(return_value=mock_richlog)
        app._handle_command = mock.MagicMock()

        # Create mock event with command input
        mock_event = mock.MagicMock()
        mock_event.value = "/help"
        mock_event.input.value = "/help"

        # Call the method
        app.on_input_submitted(mock_event)

        # Check that command handler was called
        app._handle_command.assert_called_once_with("/help")

        # Input should be cleared
        assert mock_event.input.value == ""

    def test_on_input_submitted_handles_regular_messages(self):
        """Test that non-command messages are handled appropriately."""
        app = OpenHandsApp()

        # Mock the query_one method
        mock_richlog = mock.MagicMock(spec=RichLog)
        app.query_one = mock.MagicMock(return_value=mock_richlog)

        # Create mock event with regular message
        mock_event = mock.MagicMock()
        mock_event.value = "hello world"
        mock_event.input.value = "hello world"

        # Call the method
        app.on_input_submitted(mock_event)

        # Check that both user message and placeholder response were written
        assert mock_richlog.write.call_count == 2

        # First call should be the user message
        first_call = mock_richlog.write.call_args_list[0][0][0]
        assert first_call == "\n> hello world"

        # Second call should be the placeholder message
        second_call = mock_richlog.write.call_args_list[1][0][0]
        assert "not implemented yet" in second_call

        # Input should be cleared
        assert mock_event.input.value == ""

    def test_show_help_content(self):
        """Test that help content contains expected information."""
        # Mock the RichLog widget
        mock_richlog = mock.MagicMock(spec=RichLog)

        # Call the help function directly
        show_help(mock_richlog)

        # Check help content
        help_text = mock_richlog.write.call_args[0][0]
        assert "OpenHands CLI Help" in help_text
        assert "/help" in help_text
        assert "/exit" in help_text
        assert "Display available commands" in help_text
        assert "Exit the application" in help_text
        assert "Tips:" in help_text
        assert "Type / and press Tab" in help_text

    @pytest.mark.parametrize(
        "completion_value,expected_command",
        [
            ("/help - Display available commands", "/help"),
            ("/exit - Exit the application", "/exit"),
            ("/help", "/help"),  # No description separator
            ("/exit", "/exit"),  # No description separator
            ("/custom - Some description", "/custom"),
            ("/test", "/test"),  # No separator at all
        ],
    )
    def test_command_autocomplete_apply_completion(
        self, completion_value, expected_command
    ):
        """Test that CommandAutoComplete only completes the command part."""
        # Create a mock input widget
        mock_input = mock.MagicMock(spec=Input)

        # Create CommandAutoComplete instance
        autocomplete = CommandAutoComplete(target=mock_input, candidates=COMMANDS)

        # Create a mock state
        mock_state = TargetState(text="", cursor_position=0)

        # Test completion
        autocomplete.apply_completion(completion_value, mock_state)

        # Should clear value and insert command part
        assert mock_input.value == ""
        mock_input.insert_text_at_cursor.assert_called_with(expected_command)

    @pytest.mark.parametrize(
        "text,cursor_position,expected_search_string",
        [
            # Valid slash commands
            ("/", 1, "/"),
            ("/h", 2, "/h"),
            ("/he", 3, "/he"),
            ("/help", 5, "/help"),
            ("/exit", 5, "/exit"),
            ("/unknown", 8, "/unknown"),
            # Leading whitespace should be ignored
            ("  /help", 7, "/help"),
            ("\t/exit", 6, "/exit"),
            ("   /", 4, "/"),
            # Non-slash commands should return empty string
            ("help", 4, ""),
            ("hello", 5, ""),
            ("", 0, ""),
            ("regular text", 12, ""),
            # Commands with spaces should return empty string (stop matching)
            ("/help ", 6, ""),
            ("/help arg", 9, ""),
            ("/exit now", 9, ""),
            ("/help - Display", 15, ""),
            # Cursor position tests
            ("/help", 0, ""),  # Cursor at start
            ("/help", 1, "/"),  # Cursor after slash
            ("/help", 3, "/he"),  # Cursor in middle
            # Edge cases with whitespace and spaces
            ("  /help ", 8, ""),  # Leading whitespace but has space
            (" ", 1, ""),  # Just whitespace
            ("  ", 2, ""),  # Multiple whitespace
        ],
    )
    def test_command_autocomplete_get_search_string(
        self, text, cursor_position, expected_search_string
    ):
        """Test that get_search_string returns correct search strings."""
        # Create CommandAutoComplete instance with a mock input
        mock_input = mock.MagicMock(spec=Input)
        autocomplete = CommandAutoComplete(target=mock_input, candidates=COMMANDS)

        # Create target state
        target_state = TargetState(text=text, cursor_position=cursor_position)

        # Test search string extraction
        result = autocomplete.get_search_string(target_state)
        assert result == expected_search_string
