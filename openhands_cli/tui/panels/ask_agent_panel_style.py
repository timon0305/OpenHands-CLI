"""CSS styles for the Ask Agent side panel."""

ASK_AGENT_PANEL_STYLE = """
    AskAgentPanel {
        width: 100%;
        height: auto;
        min-height: 10;
        max-height: 50%;
        padding: 0 1;
        layout: vertical;
    }

    .ask-agent-header-row {
        width: 100%;
        height: 1;
        align-vertical: middle;
        margin-bottom: 1;
    }

    .ask-agent-header {
        color: $primary;
        text-style: bold;
        width: 1fr;
        height: 1;
    }

    #ask-agent-input {
        width: 100%;
        height: 3;
        margin-bottom: 1;
    }

    #ask-agent-submit-btn {
        min-width: 8;
        width: auto;
        height: 1;
        background: $primary;
        color: $background;
        border: none;
        padding: 0 1;
        margin: 0;
    }

    #ask-agent-submit-btn:hover {
        background: $accent;
    }

    #ask-agent-submit-btn:focus {
        background: $primary;
    }

    #ask-agent-submit-btn.-active {
        background: $accent;
    }

    #ask-agent-output {
        width: 100%;
        height: auto;
        min-height: 3;
        max-height: 20;
        overflow-y: auto;
        padding: 1;
        background: $surface;
        color: $foreground;
        margin-top: 1;
    }

    .ask-agent-loading {
        color: $warning;
        text-style: italic;
    }
"""
