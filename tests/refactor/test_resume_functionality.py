"""Tests for resume functionality in the refactored UI."""

import uuid
from unittest.mock import MagicMock, patch

from openhands_cli.refactor.conversation_runner import ConversationRunner
from openhands_cli.refactor.textual_app import OpenHandsApp


class TestResumeFunctionality:
    """Test resume functionality in the refactored UI."""

    def test_textual_app_accepts_resume_conversation_id(self):
        """Test that OpenHandsApp accepts resume_conversation_id parameter."""
        test_uuid = uuid.uuid4()
        app = OpenHandsApp(resume_conversation_id=test_uuid)

        assert app.conversation_id == test_uuid

    def test_textual_app_main_accepts_resume_parameter(self):
        """Test that main function accepts resume_conversation_id parameter."""
        test_uuid = uuid.uuid4()

        with (
            patch.object(OpenHandsApp, "__init__", return_value=None) as mock_init,
            patch.object(OpenHandsApp, "run") as mock_run,
        ):
            from openhands_cli.refactor.textual_app import main

            main(resume_conversation_id=str(test_uuid))

            # Verify OpenHandsApp was initialized with the resume_conversation_id
            mock_init.assert_called_once_with(resume_conversation_id=str(test_uuid))
            mock_run.assert_called_once()

    def test_conversation_runner_initialize_with_conversation_id(self):
        """Test that ConversationRunner can initialize with a conversation ID."""
        test_uuid = uuid.uuid4()

        runner = ConversationRunner(test_uuid)

        # Verify the conversation_id was set correctly
        assert runner.conversation_id == test_uuid

    def test_simple_main_passes_resume_to_textual_main(self):
        """Test that simple_main.py passes resume argument to textual main."""
        test_uuid = uuid.uuid4()

        # Mock the argparse result
        mock_args = MagicMock()
        mock_args.command = None  # Default command
        mock_args.exp = True  # Use experimental UI
        mock_args.resume = test_uuid

        with (
            patch("openhands_cli.simple_main.create_main_parser") as mock_parser,
            patch("openhands_cli.refactor.textual_app.main") as mock_textual_main,
        ):
            mock_parser.return_value.parse_args.return_value = mock_args

            from openhands_cli.simple_main import main

            main()

            # Verify textual main was called with the resume argument
            mock_textual_main.assert_called_once_with(resume_conversation_id=test_uuid)

    @patch("openhands_cli.refactor.textual_app.ConversationRunner")
    @patch("openhands_cli.refactor.textual_app.TextualVisualizer")
    def test_app_initializes_conversation_with_resume_id(
        self, mock_visualizer_cls, mock_runner_cls
    ):
        """Test that the app initializes conversation with resume ID during
        _initialize_main_ui."""
        test_uuid = uuid.uuid4()

        # Create mock instances
        mock_visualizer = MagicMock()
        mock_visualizer_cls.return_value = mock_visualizer
        mock_runner = MagicMock()
        mock_runner_cls.return_value = mock_runner

        # Create app with resume ID
        app = OpenHandsApp(resume_conversation_id=test_uuid)

        # Mock the query_one method to return mock widgets
        app.query_one = MagicMock()
        mock_main_display = MagicMock()
        app.query_one.return_value = mock_main_display

        # Call _initialize_main_ui
        app._initialize_main_ui()

        # Verify conversation runner was created
        mock_runner_cls.assert_called_once_with(mock_visualizer)

        # Verify initialize_conversation was called with the resume ID
        mock_runner.initialize_conversation.assert_called_once_with(
            conversation_id=test_uuid
        )
