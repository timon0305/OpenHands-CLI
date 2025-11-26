"""Minimal conversation runner for the refactored UI."""

import asyncio
import uuid
from typing import Optional

from openhands.sdk import BaseConversation, Message, TextContent
from openhands_cli.setup import setup_conversation


class MinimalConversationRunner:
    """Minimal conversation runner without confirmation mode for the refactored UI."""

    def __init__(self):
        self.conversation: Optional[BaseConversation] = None
        self.conversation_id: Optional[uuid.UUID] = None
        self._running = False

    def initialize_conversation(self) -> None:
        """Initialize a new conversation."""
        self.conversation_id = uuid.uuid4()
        # Setup conversation without security analyzer (no confirmation mode)
        self.conversation = setup_conversation(
            self.conversation_id, include_security_analyzer=False
        )

    async def process_message_async(self, user_input: str) -> None:
        """Process a user message asynchronously to keep UI unblocked.
        
        Args:
            user_input: The user's message text
        """
        if not self.conversation:
            self.initialize_conversation()

        # Create message from user input
        message = Message(
            role="user",
            content=[TextContent(text=user_input)],
        )

        # Run conversation processing in a separate thread to avoid blocking UI
        await asyncio.get_event_loop().run_in_executor(
            None, self._run_conversation_sync, message
        )

    def _run_conversation_sync(self, message: Message) -> None:
        """Run the conversation synchronously in a thread.
        
        Args:
            message: The message to process
        """
        if not self.conversation:
            return

        self._running = True
        try:
            # Send message and run conversation
            self.conversation.send_message(message)
            self.conversation.run()
        finally:
            self._running = False

    @property
    def is_running(self) -> bool:
        """Check if conversation is currently running."""
        return self._running

    @property
    def current_conversation_id(self) -> Optional[str]:
        """Get the current conversation ID as a string."""
        return str(self.conversation_id) if self.conversation_id else None