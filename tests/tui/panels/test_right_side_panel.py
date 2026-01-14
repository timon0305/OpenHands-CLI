"""Tests for RightSidePanel widget."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import Button, Static

from openhands_cli.tui.panels.ask_agent_panel import AskAgentPanel
from openhands_cli.tui.panels.plan_side_panel import PlanSidePanel
from openhands_cli.tui.panels.right_side_panel import RightSidePanel


def _create_mock_app(
    conversation_dir: str | Path | None = None,
    conversation_runner: Any = None,
) -> Any:
    """Create a mock OpenHandsApp with required attributes."""
    mock_app = MagicMock()
    mock_app.conversation_dir = str(conversation_dir) if conversation_dir else ""
    mock_app.conversation_runner = conversation_runner
    mock_app.query_one = MagicMock()
    return mock_app


class RightSidePanelTestApp(App):
    """Test app for mounting RightSidePanel."""

    CSS = """
    Screen { layout: horizontal; }
    #main_content { width: 2fr; }
    """

    def __init__(
        self,
        conversation_dir: str | Path | None = None,
        conversation_runner: Any = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.conversation_dir = str(conversation_dir) if conversation_dir else ""
        self.conversation_runner = conversation_runner
        self.right_side_panel: RightSidePanel | None = None

    def compose(self) -> ComposeResult:
        with Horizontal(id="content_area"):
            yield Static("Main content", id="main_content")

    def on_mount(self) -> None:
        self.right_side_panel = RightSidePanel(self)  # type: ignore[arg-type]


class TestRightSidePanelCompose:
    """Tests for RightSidePanel compose method."""

    @pytest.mark.asyncio
    async def test_panel_contains_plan_panel(self, tmp_path: Path):
        """Verify RightSidePanel contains a PlanSidePanel."""
        app = RightSidePanelTestApp(conversation_dir=tmp_path)
        async with app.run_test() as pilot:
            await pilot.pause()

            assert app.right_side_panel is not None

            # Mount the panel
            with patch.object(app.right_side_panel, "refresh_from_disk"):
                app.right_side_panel.toggle()
                await pilot.pause()

            # Check for PlanSidePanel
            plan_panel = app.right_side_panel.query_one(PlanSidePanel)
            assert plan_panel is not None

    @pytest.mark.asyncio
    async def test_panel_contains_ask_agent_panel(self, tmp_path: Path):
        """Verify RightSidePanel contains an AskAgentPanel."""
        app = RightSidePanelTestApp(conversation_dir=tmp_path)
        async with app.run_test() as pilot:
            await pilot.pause()

            assert app.right_side_panel is not None

            # Mount the panel
            with patch.object(app.right_side_panel, "refresh_from_disk"):
                app.right_side_panel.toggle()
                await pilot.pause()

            # Check for AskAgentPanel
            ask_panel = app.right_side_panel.query_one(AskAgentPanel)
            assert ask_panel is not None

    @pytest.mark.asyncio
    async def test_panel_contains_divider(self, tmp_path: Path):
        """Verify RightSidePanel contains a divider between panels."""
        app = RightSidePanelTestApp(conversation_dir=tmp_path)
        async with app.run_test() as pilot:
            await pilot.pause()

            assert app.right_side_panel is not None

            # Mount the panel
            with patch.object(app.right_side_panel, "refresh_from_disk"):
                app.right_side_panel.toggle()
                await pilot.pause()

            # Check for divider
            divider = app.right_side_panel.query_one(".right-panel-divider", Static)
            assert divider is not None

    @pytest.mark.asyncio
    async def test_panel_has_close_button(self, tmp_path: Path):
        """Verify RightSidePanel has a close button."""
        app = RightSidePanelTestApp(conversation_dir=tmp_path)
        async with app.run_test() as pilot:
            await pilot.pause()

            assert app.right_side_panel is not None

            # Mount the panel
            with patch.object(app.right_side_panel, "refresh_from_disk"):
                app.right_side_panel.toggle()
                await pilot.pause()

            # Check for close button
            close_btn = app.right_side_panel.query_one("#right-panel-close-btn", Button)
            assert close_btn is not None


class TestRightSidePanelToggle:
    """Tests for RightSidePanel toggle method."""

    @pytest.mark.asyncio
    async def test_mounts_panel_when_not_on_screen(self, tmp_path: Path):
        """Verify toggle() mounts the panel when not on screen."""
        app = RightSidePanelTestApp(conversation_dir=tmp_path)
        async with app.run_test() as pilot:
            await pilot.pause()

            assert app.right_side_panel is not None
            assert app.right_side_panel.is_on_screen is False

            # Toggle to mount
            with patch.object(app.right_side_panel, "refresh_from_disk"):
                app.right_side_panel.toggle()
                await pilot.pause()

            assert app.right_side_panel.is_on_screen is True

    @pytest.mark.asyncio
    async def test_removes_panel_when_on_screen(self, tmp_path: Path):
        """Verify toggle() removes the panel when on screen."""
        app = RightSidePanelTestApp(conversation_dir=tmp_path)
        async with app.run_test() as pilot:
            await pilot.pause()

            assert app.right_side_panel is not None

            # Mount first
            with patch.object(app.right_side_panel, "refresh_from_disk"):
                app.right_side_panel.toggle()
                await pilot.pause()
                assert app.right_side_panel.is_on_screen is True

            # Toggle to remove
            app.right_side_panel.toggle()
            await pilot.pause()

            assert app.right_side_panel.is_on_screen is False

    @pytest.mark.asyncio
    async def test_sets_user_dismissed_flag(self, tmp_path: Path):
        """Verify toggle() sets user_dismissed flag when removing panel."""
        app = RightSidePanelTestApp(conversation_dir=tmp_path)
        async with app.run_test() as pilot:
            await pilot.pause()

            assert app.right_side_panel is not None

            # Mount first
            with patch.object(app.right_side_panel, "refresh_from_disk"):
                app.right_side_panel.toggle()
                await pilot.pause()

            assert app.right_side_panel.user_dismissed is False

            # Toggle to remove
            app.right_side_panel.toggle()
            await pilot.pause()

            assert app.right_side_panel.user_dismissed is True


class TestRightSidePanelRefresh:
    """Tests for RightSidePanel refresh_from_disk method."""

    @pytest.mark.asyncio
    async def test_refresh_calls_plan_panel_refresh(self, tmp_path: Path):
        """Verify refresh_from_disk calls plan panel's refresh method."""
        # Create tasks file
        tasks_data = [{"title": "Test Task", "status": "in_progress"}]
        tasks_file = tmp_path / "TASKS.json"
        tasks_file.write_text(json.dumps(tasks_data))

        app = RightSidePanelTestApp(conversation_dir=tmp_path)
        async with app.run_test() as pilot:
            await pilot.pause()

            assert app.right_side_panel is not None

            # Mount the panel (this calls refresh_from_disk internally)
            app.right_side_panel.toggle()
            await pilot.pause()

            # Get the plan panel
            plan_panel = app.right_side_panel.plan_panel
            assert plan_panel is not None

            # Manually call refresh to load tasks (since compose happens after toggle)
            app.right_side_panel.refresh_from_disk()
            await pilot.pause()

            # Verify tasks were loaded
            assert len(plan_panel.task_list) == 1
            assert plan_panel.task_list[0].title == "Test Task"


class TestRightSidePanelCloseButton:
    """Tests for close button functionality."""

    @pytest.mark.asyncio
    async def test_close_button_removes_panel(self, tmp_path: Path):
        """Verify clicking close button removes the panel."""
        app = RightSidePanelTestApp(conversation_dir=tmp_path)
        async with app.run_test() as pilot:
            await pilot.pause()

            assert app.right_side_panel is not None

            # Mount the panel
            with patch.object(app.right_side_panel, "refresh_from_disk"):
                app.right_side_panel.toggle()
                await pilot.pause()

            assert app.right_side_panel.is_on_screen is True

            # Click close button - need to use the button's press method
            close_btn = app.right_side_panel.query_one("#right-panel-close-btn", Button)
            close_btn.press()
            await pilot.pause()

            assert app.right_side_panel.is_on_screen is False
