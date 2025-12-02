"""Command provider for MCP-related commands in the command palette."""

from textual.command import Hit, Hits, Provider


class MCPCommandProvider(Provider):
    """Command provider for MCP-related commands."""

    async def search(self, query: str) -> Hits:
        """Search for MCP-related commands.
        
        Args:
            query: The search query from the command palette
            
        Yields:
            Hit objects for matching commands
        """
        matcher = self.matcher(query)
        
        # MCP command
        command = "MCP"
        score = matcher.match(command)
        if score > 0:
            yield Hit(
                score,
                matcher.highlight(command),
                self.app.action_toggle_mcp_panel,
                help="Toggle MCP servers panel"
            )