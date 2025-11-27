"""Tests for RichLogVisualizer integration."""

import unittest
from unittest import mock

from openhands_cli.refactor.richlog_visualizer import RichLogVisualizer


class TestRichLogVisualizer(unittest.TestCase):
    """Test the RichLogVisualizer class."""

    def setUp(self):
        """Set up test fixtures."""
        self.write_callback = mock.MagicMock()
        self.visualizer = RichLogVisualizer(
            write_callback=self.write_callback,
            skip_user_messages=False
        )

    def test_visualizer_initialization(self):
        """Test that the visualizer initializes correctly."""
        self.assertIsNotNone(self.visualizer)
        self.assertEqual(self.visualizer._write_callback, self.write_callback)
        self.assertFalse(self.visualizer._skip_user_messages)

    def test_visualizer_with_skip_user_messages(self):
        """Test that skip_user_messages option is set correctly."""
        visualizer = RichLogVisualizer(
            write_callback=self.write_callback,
            skip_user_messages=True
        )
        self.assertTrue(visualizer._skip_user_messages)

    def test_on_event_with_unknown_event(self):
        """Test that on_event handles unknown events gracefully."""
        # Create a mock event that won't be in the visualization config
        mock_event = mock.MagicMock()
        mock_event.__class__.__name__ = "UnknownEvent"
        
        # Should not raise an exception
        try:
            self.visualizer.on_event(mock_event)
        except Exception as e:
            self.fail(f"on_event raised an exception: {e}")
        
        # Callback should not be called for unknown events
        self.write_callback.assert_not_called()

    def test_write_callback_is_stored(self):
        """Test that the write callback is properly stored."""
        self.assertEqual(self.visualizer._write_callback, self.write_callback)

    def test_visualizer_inheritance(self):
        """Test that RichLogVisualizer inherits from ConversationVisualizerBase."""
        from openhands.sdk.conversation.visualizer.base import ConversationVisualizerBase
        self.assertIsInstance(self.visualizer, ConversationVisualizerBase)


if __name__ == "__main__":
    unittest.main()