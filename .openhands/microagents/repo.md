# Repository Purpose
This is the OpenHands CLI - a command-line interface for OpenHands AI Agent with Terminal User Interface (TUI) support. It provides a standalone executable that allows users to interact with OpenHands through a terminal interface.

This project ports CLI code from `https://github.com/All-Hands-AI/OpenHands` (folder `openhands/cli`) and refactors it to use the new agent-sdk from `https://github.com/All-Hands-AI/agent-sdk`.

## References
- Example script for agent-sdk: `https://github.com/All-Hands-AI/agent-sdk/blob/main/examples/hello_world.py`
- Use `$GITHUB_TOKEN` to refer to OpenHands repo for copying UI and user interactions for the CLI
- Refer to agent-sdk repo for setting up agent behavior, tools, etc.

# Setup Instructions
To set up the development environment:
1. Install dependencies: `make install-dev`
2. Install pre-commit hooks: `make install-pre-commit-hooks`



# Development Guidelines

## Linting Requirements
**Always run lint before committing changes.** Use `make lint` to run all pre-commit hooks on all files. The project uses:

## Typing Requirements
When using types, prefer modern typing syntax (e.g., use `| None` instead of `Optional`).

## Documentation Guidelines
- **Do NOT send summary updates in the README.md** for the repository
- **Do NOT create .md files in the root** of the repository to track or send updates
- Only make documentation changes when explicitly requested to

## Updating Agent-SDK SHA

If the user says something along the lines of "update the sha" or "update the agent-sdk sha", you need to:

1. Use the `$GITHUB_TOKEN` to get the latest commit from the agent-sdk repository
2. Update the poetry toml file with the new SHA
3. Regenerate the uv lock file
4. Run `./build.sh` to confirm that the build still works
5. Open a pull request with the changes

If the build fails, still open the pull request and explain what error you're seeing, and the steps you plan to take to fix it; don't fix it yet though.

# TUI Testing and Debugging with Screenshots

This project uses Textual for the Terminal User Interface (TUI). You can test and debug the TUI by capturing SVG screenshots and viewing them in a browser.

## How It Works

The TUI testing approach uses:
1. **Textual's `run_test()` + Pilot API** - Like Playwright but for terminal UIs
2. **SVG Screenshots** - `app.export_screenshot()` generates viewable images of the terminal
3. **Headless Mode** - Tests run without needing an actual terminal

## Writing TUI Tests with Screenshots

```python
import pytest
from openhands_cli.refactor.modals import SettingsScreen
from openhands_cli.refactor.textual_app import OpenHandsApp

@pytest.mark.asyncio
async def test_ui_screenshot(monkeypatch):
    # Skip initial settings setup for testing
    monkeypatch.setattr(SettingsScreen, "is_initial_setup_required", lambda: False)
    
    app = OpenHandsApp(exit_confirmation=False)
    
    async with app.run_test(size=(120, 40)) as pilot:
        # Wait for UI to render
        await pilot.pause()
        
        # Simulate user interactions (like Playwright)
        await pilot.press("h", "e", "l", "l", "o")  # Type text
        await pilot.press("enter")                   # Press Enter
        await pilot.click("#some-widget")            # Click by CSS selector
        
        # Capture screenshot as SVG
        svg_content = app.export_screenshot(title="My Test Screenshot")
        
        # Save to a persistent location for viewing
        from pathlib import Path
        screenshot_dir = Path("/tmp/tui_screenshots")
        screenshot_dir.mkdir(exist_ok=True)
        (screenshot_dir / "my_screenshot.svg").write_text(svg_content)
```

## Viewing Screenshots

### Option 1: Start HTTP Server and View in Browser
```bash
# Start a simple HTTP server to serve the screenshots
cd /tmp/tui_screenshots && python3 -m http.server 12000 --bind 0.0.0.0 &

# Then open in browser (use the runtime URL):
# https://work-1-<your-runtime-id>.prod-runtime.all-hands.dev/my_screenshot.svg
```

### Option 2: Use the Browser Tool
After saving screenshots, use the browser tool to navigate to the served SVG:
```python
goto("https://work-1-<runtime-id>.prod-runtime.all-hands.dev/my_screenshot.svg")
```

## Pilot API Reference (Playwright-like for Terminals)

| Method | Description | Example |
|--------|-------------|---------|
| `pilot.press(*keys)` | Simulate key presses | `await pilot.press("ctrl+l")` |
| `pilot.click(selector)` | Click on a widget | `await pilot.click("#button-id")` |
| `pilot.hover(selector)` | Hover over a widget | `await pilot.hover("#menu")` |
| `pilot.pause()` | Wait for pending messages | `await pilot.pause()` |

## Example Test File

See `tests/refactor/test_tui_screenshot.py` for comprehensive examples including:
- Capturing initial UI state
- Testing UI after user input
- Testing at different terminal sizes
- Full UI flow with multiple screenshots

## Running TUI Tests

```bash
# Run all TUI screenshot tests
uv run pytest tests/refactor/test_tui_screenshot.py -v

# Screenshots will be saved to /tmp/tui_screenshots/
```

## Snapshot Testing (Visual Regression)

For automated visual regression testing, install `pytest-textual-snapshot`:
```bash
uv pip install pytest-textual-snapshot
```

Then use the `snap_compare` fixture to automatically compare screenshots between test runs.