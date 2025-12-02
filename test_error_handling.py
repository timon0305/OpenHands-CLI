#!/usr/bin/env python3
"""Test error handling when agent fails to load."""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Static

from openhands_cli.refactor.mcp_side_panel import MCPSidePanel
from openhands_cli.refactor.theme import OPENHANDS_THEME


class ErrorHandlingTest(App):
    """Test app for MCP error handling."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.register_theme(OPENHANDS_THEME)
        self.theme = "openhands"

    CSS = """
    Screen {
        layout: vertical;
        background: $background;
    }

    #main_area {
        height: 1fr;
        layout: horizontal;
    }

    #content {
        width: 1fr;
        height: 100%;
        background: $background;
        padding: 2;
    }

    #controls {
        height: 5;
        background: $surface;
        padding: 1;
    }

    Button {
        margin: 0 1;
    }
    """

    def compose(self) -> ComposeResult:
        """Compose the test app."""
        with Horizontal(id="main_area"):
            with Vertical(id="content"):
                yield Static("MCP Error Handling Test", classes="header")
                yield Static("Testing MCP panel with None agent (simulating load failure)")
                yield Static("")
                yield Static("Expected behavior:")
                yield Static("- Panel should show error message")
                yield Static("- Error should be in red color")
                yield Static("- Should mention corrupted agent settings")
        
            # Create MCP panel with None agent to simulate load failure
            yield MCPSidePanel(agent=None)
        
        with Vertical(id="controls"):
            yield Button("Quit", id="quit")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "quit":
            self.exit()


def main():
    """Run the error handling test."""
    print("MCP Error Handling Test")
    print("=======================")
    print("This test verifies error handling when agent fails to load.")
    print("The MCP panel should display an error message.")
    print()
    
    app = ErrorHandlingTest()
    app.run()


if __name__ == "__main__":
    main()