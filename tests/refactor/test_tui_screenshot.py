"""
Proof-of-concept tests for TUI screenshot testing.

This module demonstrates how to test the textual UI by:
1. Running the app in headless mode using Textual's run_test() 
2. Interacting with the UI via the Pilot API (like Playwright for terminals)
3. Taking SVG screenshots that can be viewed/compared

The approach uses Textual's built-in testing framework which provides:
- Pilot: An API similar to Playwright for simulating user interactions
- Screenshot export: SVG screenshots that can be saved and compared
- Headless mode: No actual terminal needed for testing
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from openhands_cli.refactor.modals import SettingsScreen
from openhands_cli.refactor.textual_app import OpenHandsApp


class TestTUIScreenshots:
    """Tests demonstrating TUI screenshot capabilities."""

    @pytest.fixture
    def screenshot_dir(self) -> Path:
        """Create a temporary directory for screenshots."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.mark.asyncio
    async def test_initial_ui_screenshot(
        self,
        monkeypatch: pytest.MonkeyPatch,
        screenshot_dir: Path,
    ) -> None:
        """
        Test that we can capture a screenshot of the initial UI state.
        
        This demonstrates:
        1. Running the app in test mode
        2. Capturing an SVG screenshot
        3. Saving it to a file for inspection
        """
        # Skip initial settings setup
        monkeypatch.setattr(
            SettingsScreen,
            "is_initial_setup_required",
            lambda: False,
        )

        app = OpenHandsApp(exit_confirmation=False)

        async with app.run_test(size=(120, 40)) as pilot:
            # Wait for the app to fully render
            await pilot.pause()

            # Export screenshot as SVG string
            svg_content = app.export_screenshot(title="OpenHands CLI - Initial State")

            # Save to file
            screenshot_path = screenshot_dir / "initial_state.svg"
            screenshot_path.write_text(svg_content)

            # Verify screenshot was created and has content
            assert screenshot_path.exists()
            assert len(svg_content) > 1000  # SVG should have substantial content
            assert "<svg" in svg_content
            assert "</svg>" in svg_content

            # Print path for manual inspection
            print(f"\nScreenshot saved to: {screenshot_path}")

    @pytest.mark.asyncio
    async def test_ui_after_typing_message(
        self,
        monkeypatch: pytest.MonkeyPatch,
        screenshot_dir: Path,
    ) -> None:
        """
        Test UI state after typing a message in the input field.
        
        This demonstrates using the Pilot API to simulate user input.
        """
        monkeypatch.setattr(
            SettingsScreen,
            "is_initial_setup_required",
            lambda: False,
        )

        app = OpenHandsApp(exit_confirmation=False)

        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()

            # Focus the input field and type a message
            # The InputField should be focused by default
            await pilot.press("h", "e", "l", "l", "o", " ", "w", "o", "r", "l", "d")
            await pilot.pause()

            # Take screenshot after typing
            svg_content = app.export_screenshot(title="OpenHands CLI - After Typing")
            screenshot_path = screenshot_dir / "after_typing.svg"
            screenshot_path.write_text(svg_content)

            assert screenshot_path.exists()
            print(f"\nScreenshot saved to: {screenshot_path}")

    @pytest.mark.asyncio
    async def test_ui_help_command(
        self,
        monkeypatch: pytest.MonkeyPatch,
        screenshot_dir: Path,
    ) -> None:
        """
        Test UI state after executing the /help command.
        
        This demonstrates:
        1. Typing a command
        2. Pressing Enter to submit
        3. Capturing the resulting UI state
        """
        monkeypatch.setattr(
            SettingsScreen,
            "is_initial_setup_required",
            lambda: False,
        )

        app = OpenHandsApp(exit_confirmation=False)

        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()

            # Type /help command
            await pilot.press("/", "h", "e", "l", "p")
            await pilot.pause()

            # Take screenshot before submitting
            svg_before = app.export_screenshot(title="OpenHands CLI - Before Help")
            (screenshot_dir / "before_help.svg").write_text(svg_before)

            # Submit the command
            await pilot.press("enter")
            await pilot.pause()

            # Take screenshot after help is displayed
            svg_after = app.export_screenshot(title="OpenHands CLI - After Help")
            screenshot_path = screenshot_dir / "after_help.svg"
            screenshot_path.write_text(svg_after)

            assert screenshot_path.exists()
            print(f"\nScreenshot saved to: {screenshot_path}")

    @pytest.mark.asyncio
    async def test_ui_different_sizes(
        self,
        monkeypatch: pytest.MonkeyPatch,
        screenshot_dir: Path,
    ) -> None:
        """
        Test UI rendering at different terminal sizes.
        
        This demonstrates testing responsive behavior.
        """
        monkeypatch.setattr(
            SettingsScreen,
            "is_initial_setup_required",
            lambda: False,
        )

        sizes = [
            (80, 24),   # Standard terminal
            (120, 40),  # Large terminal
            (60, 20),   # Small terminal
        ]

        for width, height in sizes:
            app = OpenHandsApp(exit_confirmation=False)

            async with app.run_test(size=(width, height)) as pilot:
                await pilot.pause()

                svg_content = app.export_screenshot(
                    title=f"OpenHands CLI - {width}x{height}"
                )
                screenshot_path = screenshot_dir / f"size_{width}x{height}.svg"
                screenshot_path.write_text(svg_content)

                assert screenshot_path.exists()
                print(f"\nScreenshot saved to: {screenshot_path}")


class TestTUIInteractions:
    """Tests demonstrating TUI interaction capabilities via Pilot API."""

    @pytest.mark.asyncio
    async def test_keyboard_navigation(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """
        Test keyboard navigation through the UI.
        
        The Pilot API allows simulating:
        - Key presses (pilot.press)
        - Mouse clicks (pilot.click)
        - Hovering (pilot.hover)
        """
        monkeypatch.setattr(
            SettingsScreen,
            "is_initial_setup_required",
            lambda: False,
        )

        app = OpenHandsApp(exit_confirmation=False)

        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()

            # Test Tab navigation
            await pilot.press("tab")
            await pilot.pause()

            # Test Escape key
            await pilot.press("escape")
            await pilot.pause()

            # Verify app is still running
            assert app.is_running

    @pytest.mark.asyncio
    async def test_input_field_interaction(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """
        Test direct interaction with the input field widget.
        """
        monkeypatch.setattr(
            SettingsScreen,
            "is_initial_setup_required",
            lambda: False,
        )

        app = OpenHandsApp(exit_confirmation=False)

        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()

            # Get the input field widget
            input_field = app.input_field

            # Verify it exists
            assert input_field is not None

            # Type into it
            await pilot.press("t", "e", "s", "t")
            await pilot.pause()

            # Check the value
            current_value = input_field.get_current_value()
            assert "test" in current_value.lower()


class TestTUIWithPersistentScreenshots:
    """
    Tests that save screenshots to a persistent location for manual review.
    
    These tests save screenshots to /tmp/tui_screenshots/ so they can be
    viewed after the test run.
    """

    @pytest.fixture
    def persistent_screenshot_dir(self) -> Path:
        """Create a persistent directory for screenshots."""
        screenshot_dir = Path("/tmp/tui_screenshots")
        screenshot_dir.mkdir(exist_ok=True)
        return screenshot_dir

    @pytest.mark.asyncio
    async def test_capture_full_ui_flow(
        self,
        monkeypatch: pytest.MonkeyPatch,
        persistent_screenshot_dir: Path,
    ) -> None:
        """
        Capture a full UI flow with multiple screenshots.
        
        Screenshots are saved to /tmp/tui_screenshots/ for manual review.
        """
        monkeypatch.setattr(
            SettingsScreen,
            "is_initial_setup_required",
            lambda: False,
        )

        app = OpenHandsApp(exit_confirmation=False)

        async with app.run_test(size=(120, 40)) as pilot:
            # Step 1: Initial state
            await pilot.pause()
            svg = app.export_screenshot(title="Step 1: Initial State")
            (persistent_screenshot_dir / "step1_initial.svg").write_text(svg)

            # Step 2: Type a message
            await pilot.press("H", "e", "l", "l", "o", " ", "A", "I")
            await pilot.pause()
            svg = app.export_screenshot(title="Step 2: After Typing")
            (persistent_screenshot_dir / "step2_typing.svg").write_text(svg)

            # Step 3: Clear and type /help
            # Clear the input by pressing backspace multiple times
            for _ in range(10):
                await pilot.press("backspace")
            await pilot.pause()

            await pilot.press("/", "h", "e", "l", "p")
            await pilot.pause()
            svg = app.export_screenshot(title="Step 3: Help Command")
            (persistent_screenshot_dir / "step3_help_command.svg").write_text(svg)

            # Step 4: Submit help command
            await pilot.press("enter")
            await pilot.pause()
            svg = app.export_screenshot(title="Step 4: Help Output")
            (persistent_screenshot_dir / "step4_help_output.svg").write_text(svg)

            print(f"\n\nScreenshots saved to: {persistent_screenshot_dir}")
            print("Files created:")
            for f in sorted(persistent_screenshot_dir.glob("*.svg")):
                print(f"  - {f.name}")
