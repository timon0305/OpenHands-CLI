"""OpenHands custom theme for textual UI."""

from textual.theme import Theme


def create_openhands_theme() -> Theme:
    """Create and return the custom OpenHands theme."""
    return Theme(
        name="openhands",
        primary="#ffe165",  # Logo, cursor color, user messages
        secondary="#ffffff",  # Borders, plain text
        accent="#277dff",  # Special text like "initialize conversation", agent messages
        foreground="#ffffff",  # Default text color
        background="#222222",  # Background color
        surface="#2a2a2a",  # Surface color (slightly lighter than background)
        panel="#222222",  # Panel color (same as background)
        success="#4ade80",  # Success messages (green)
        warning="#fbbf24",  # Warning messages (amber/orange)
        error="#ff6b6b",  # Error messages (light red)
        dark=True,  # This is a dark theme
        variables={
            # Placeholder text color
            "input-placeholder-foreground": "#727987",
            # Selection colors
            "input-selection-background": "#ffe165 20%",
        },
    )


# Create the theme instance
OPENHANDS_THEME = create_openhands_theme()
