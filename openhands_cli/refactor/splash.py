"""Welcome message utilities for OpenHands CLI textual app."""

import uuid

from rich.console import Console
from rich.panel import Panel
from textual.theme import Theme

from openhands_cli.version_check import check_for_updates


def get_openhands_banner() -> str:
    """Get the OpenHands ASCII art banner."""
    return r"""     ___                    _   _                 _
    /  _ \ _ __   ___ _ __ | | | | __ _ _ __   __| |___
    | | | | '_ \ / _ \ '_ \| |_| |/ _` | '_ \ / _` / __|
    | |_| | |_) |  __/ | | |  _  | (_| | | | | (_| \__ \
    \___ /| .__/ \___|_| |_|_| |_|\__,_|_| |_|\__,_|___/
          |_|"""


def get_splash_content(conversation_id: str | None = None, *, theme: Theme) -> dict:
    """Get structured splash screen content for native Textual widgets.

    Args:
        conversation_id: Optional conversation ID to display
        theme: Theme to use for colors
    """
    # Use theme colors
    primary_color = theme.primary
    accent_color = theme.accent

    # Generate UUID if no conversation_id provided
    if conversation_id is None:
        conversation_id = str(uuid.uuid4())

    # Use Rich markup for colored banner (apply color to each line)
    banner_lines = get_openhands_banner().split("\n")
    colored_banner_lines = [f"[{primary_color}]{line}[/]" for line in banner_lines]
    banner = "\n".join(colored_banner_lines)

    # Get version information
    version_info = check_for_updates()

    # Create structured content as dictionary
    content = {
        "banner": banner,
        "version": f"OpenHands CLI v{version_info.current_version}",
        "status_text": "All set up!",
        "conversation_text": f"[{accent_color}]Initialized conversation[/] {conversation_id}",
        "conversation_id": conversation_id,
        "instructions_header": f"[{primary_color}]What do you want to build?[/]",
        "instructions": [
            "1. Ask questions, edit files, or run commands.",
            "2. Use @ to look up a file in the folder structure",
            "3. Type /help for help or / to immediately scroll through available commands"
        ],
        "update_notice": None
    }

    # Add update notification if needed
    if version_info.needs_update and version_info.latest_version:
        content["update_notice"] = (
            f"[{primary_color}]⚠ Update available: {version_info.latest_version}[/]\n"
            "Run 'uv tool upgrade openhands' to update"
        )

    return content


def get_welcome_message(conversation_id: str | None = None, *, theme: Theme) -> str:
    """Get the complete welcome message with version info.

    Args:
        conversation_id: Optional conversation ID to display
        theme: Theme to use for colors
    """
    # Use theme colors
    primary_color = theme.primary
    accent_color = theme.accent
    background_color = theme.background

    # Generate UUID if no conversation_id provided
    if conversation_id is None:
        conversation_id = str(uuid.uuid4())

    # Use Rich markup for colored banner (apply color to each line)
    banner_lines = get_openhands_banner().split("\n")
    colored_banner_lines = [f"[{primary_color}]{line}[/]" for line in banner_lines]
    banner = "\n".join(colored_banner_lines)

    # Get version information
    version_info = check_for_updates()

    message_parts = [banner, ""]

    # Version line
    message_parts.append(f"OpenHands CLI v{version_info.current_version}")

    # Create console for rendering panels with app background
    console = Console(width=80, legacy_windows=False)

    # Status panel
    status_panel = Panel("All set up!", width=15, style=f"on {background_color}")
    with console.capture() as capture:
        console.print(status_panel)
    message_parts.extend(["", capture.get(), ""])

    # Conversation ID panel (always show now)
    conv_text = f"[{accent_color}]Initialized conversation[/] {conversation_id}"
    conv_panel = Panel(conv_text, style=f"on {background_color}")
    with console.capture() as capture:
        console.print(conv_panel)
    message_parts.extend([capture.get(), ""])

    # Instructions
    message_parts.extend(
        [
            f"[{primary_color}]What do you want to build?[/]",
            "1. Ask questions, edit files, or run commands.",
            "2. Use @ to look up a file in the folder structure",
            "3. Type /help for help or / to immediately scroll through available "
            "commands",
        ]
    )

    # Update notification (if needed)
    if version_info.needs_update and version_info.latest_version:
        message_parts.extend(
            [
                "",
                f"[{primary_color}]⚠ Update available: "
                f"{version_info.latest_version}[/]",
                "Run 'uv tool upgrade openhands' to update",
            ]
        )

    return "\n".join(message_parts)
