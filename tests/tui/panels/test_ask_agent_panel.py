"""Tests for AskAgentPanel widget."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import Button, Input, Static

from openhands_cli.tui.panels.ask_agent_panel import AskAgentPanel


def _create_mock_app(
    conversation_runner: Any = None,
) -> Any:
    """Create a mock OpenHandsApp with required attributes."""
    mock_app = MagicMock()
    mock_app.conversation_runner = conversation_runner
    return mock_app


class AskAgentPanelTestApp(App):
    """Test app for mounting AskAgentPanel."""

    CSS = """
    Screen { layout: horizontal; }
    #main_content { width: 2fr; }
    """

    def __init__(self, conversation_runner: Any = None, **kwargs):
        super().__init__(**kwargs)
        self.conversation_runner = conversation_runner
        self.ask_agent_panel: AskAgentPanel | None = None

    def compose(self) -> ComposeResult:
        with Horizontal(id="content_area"):
            yield Static("Main content", id="main_content")

    def on_mount(self) -> None:
        self.ask_agent_panel = AskAgentPanel(self)  # type: ignore[arg-type]
        content_area = self.query_one("#content_area", Horizontal)
        content_area.mount(self.ask_agent_panel)


class TestAskAgentPanelCompose:
    """Tests for AskAgentPanel compose method."""

    @pytest.mark.asyncio
    async def test_panel_has_input_field(self):
        """Verify panel contains an input field for questions."""
        app = AskAgentPanelTestApp()
        async with app.run_test() as pilot:
            await pilot.pause()

            assert app.ask_agent_panel is not None
            input_widget = app.ask_agent_panel.query_one("#ask-agent-input", Input)
            assert input_widget is not None
            assert "question" in input_widget.placeholder.lower()

    @pytest.mark.asyncio
    async def test_panel_has_submit_button(self):
        """Verify panel contains a submit button."""
        app = AskAgentPanelTestApp()
        async with app.run_test() as pilot:
            await pilot.pause()

            assert app.ask_agent_panel is not None
            button = app.ask_agent_panel.query_one("#ask-agent-submit-btn", Button)
            assert button is not None
            assert button.label.plain == "Ask"

    @pytest.mark.asyncio
    async def test_panel_has_output_area(self):
        """Verify panel contains an output area for responses."""
        app = AskAgentPanelTestApp()
        async with app.run_test() as pilot:
            await pilot.pause()

            assert app.ask_agent_panel is not None
            output = app.ask_agent_panel.query_one("#ask-agent-output", Static)
            assert output is not None

    @pytest.mark.asyncio
    async def test_panel_has_header(self):
        """Verify panel contains a header."""
        app = AskAgentPanelTestApp()
        async with app.run_test() as pilot:
            await pilot.pause()

            assert app.ask_agent_panel is not None
            header = app.ask_agent_panel.query_one(".ask-agent-header", Static)
            assert header is not None


class TestAskAgentPanelSubmission:
    """Tests for AskAgentPanel question submission."""

    @pytest.mark.asyncio
    async def test_empty_question_not_submitted(self):
        """Verify empty questions are not submitted."""
        mock_runner = MagicMock()
        mock_runner.conversation = MagicMock()
        mock_runner.conversation.ask_agent = MagicMock(return_value="response")

        app = AskAgentPanelTestApp(conversation_runner=mock_runner)
        async with app.run_test() as pilot:
            await pilot.pause()

            assert app.ask_agent_panel is not None

            # Click submit with empty input
            button = app.ask_agent_panel.query_one("#ask-agent-submit-btn", Button)
            await pilot.click(button)
            await pilot.pause()

            # ask_agent should not be called
            mock_runner.conversation.ask_agent.assert_not_called()

    @pytest.mark.asyncio
    async def test_shows_error_when_no_conversation_runner(self):
        """Verify error message when no conversation runner exists."""
        app = AskAgentPanelTestApp(conversation_runner=None)
        async with app.run_test() as pilot:
            await pilot.pause()

            assert app.ask_agent_panel is not None

            # Enter a question
            input_widget = app.ask_agent_panel.query_one("#ask-agent-input", Input)
            input_widget.value = "Test question"

            # Submit
            button = app.ask_agent_panel.query_one("#ask-agent-submit-btn", Button)
            await pilot.click(button)
            await pilot.pause()

            # Check output shows error - use render() to get the content
            output = app.ask_agent_panel.query_one("#ask-agent-output", Static)
            # The output should contain error message about no active conversation
            output_text = str(output.render())
            assert "No active conversation" in output_text


class TestAskAgentPanelInputClearing:
    """Tests for input clearing behavior."""

    @pytest.mark.asyncio
    async def test_input_cleared_after_submission(self):
        """Verify input is cleared after submitting a question."""
        mock_runner = MagicMock()
        mock_runner.conversation = MagicMock()
        mock_runner.conversation.ask_agent = MagicMock(return_value="response")

        app = AskAgentPanelTestApp(conversation_runner=mock_runner)
        async with app.run_test() as pilot:
            await pilot.pause()

            assert app.ask_agent_panel is not None

            # Enter a question
            input_widget = app.ask_agent_panel.query_one("#ask-agent-input", Input)
            input_widget.value = "Test question"

            # Submit
            app.ask_agent_panel._submit_question()
            await pilot.pause()

            # Input should be cleared
            assert input_widget.value == ""
