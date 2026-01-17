"""Centralized state management for OpenHands TUI.

This module provides a message-based state management system. The StateManager
holds all conversation state and emits Textual messages when state changes.
UI widgets listen for these messages and update accordingly.

Usage:
    # In app:
    state_manager = StateManager()
    
    # Widgets listen for state changes via message handlers:
    @on(StateChanged)
    def _on_state_changed(self, event: StateChanged) -> None:
        if event.key == "is_running":
            self._update_display()
    
    # Update state (triggers message emission):
    state_manager.set_running(True)
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from textual.message import Message
from textual.reactive import var
from textual.widget import Widget

if TYPE_CHECKING:
    from openhands.sdk.event import ActionEvent


@dataclass
class ConversationMetrics:
    """Metrics for the current conversation."""
    input_tokens: int = 0
    output_tokens: int = 0
    cache_hit_rate: str = "N/A"
    last_request_input_tokens: int = 0
    context_window: int = 0
    accumulated_cost: float = 0.0


@dataclass
class ConversationStateSnapshot:
    """Immutable snapshot of conversation state.
    
    This dataclass holds the complete state of a conversation at a point in time.
    Used for state transitions and history tracking.
    """
    is_running: bool = False
    is_confirmation_mode: bool = True
    cloud_ready: bool = True
    cloud_mode: bool = False
    elapsed_seconds: int = 0
    pending_actions_count: int = 0
    metrics: ConversationMetrics = field(default_factory=ConversationMetrics)


class StateChanged(Message):
    """Message emitted when conversation state changes.
    
    Widgets can listen to this message for complex state change reactions
    that can't be handled by simple reactive bindings.
    """
    def __init__(self, key: str, old_value: Any, new_value: Any) -> None:
        super().__init__()
        self.key = key
        self.old_value = old_value
        self.new_value = new_value


class ConversationFinished(Message):
    """Message emitted when conversation finishes running."""
    pass


class ConversationStarted(Message):
    """Message emitted when conversation starts running."""
    pass


class ConfirmationRequired(Message):
    """Message emitted when actions require user confirmation."""
    def __init__(self, pending_actions: list["ActionEvent"]) -> None:
        super().__init__()
        self.pending_actions = pending_actions


class StateManager:
    """Centralized state manager for conversation UI.
    
    This class manages conversation state and updates the App's reactive
    properties. Child widgets use data_bind() to bind to the App's properties.
    
    Example:
        # In App.__init__:
        self.state_manager = StateManager(self)
        
        # In compose():
        yield WorkingStatusLine().data_bind(
            is_running=OpenHandsApp.is_running,
            elapsed_seconds=OpenHandsApp.elapsed_seconds,
        )
        
        # State updates propagate to bound children:
        state_manager.set_running(True)  # Updates App.is_running -> WorkingStatusLine
    
    The StateManager also posts messages for complex state transitions.
    """
    
    def __init__(self, app, cloud_mode: bool = False) -> None:
        self._app = app
        self._cloud_mode = cloud_mode
        self._cloud_ready = not cloud_mode
        self._is_confirmation_mode = True
        self._pending_actions_count = 0
        self._conversation_start_time: float | None = None
        self._timer = None
    
    @property
    def is_running(self) -> bool:
        """Get current running state from App."""
        return self._app.is_running
    
    def start_timer(self) -> None:
        """Start the elapsed time timer. Call this from App.on_mount()."""
        self._timer = self._app.set_interval(1.0, self._update_elapsed)
    
    def stop_timer(self) -> None:
        """Stop the elapsed time timer."""
        if self._timer:
            self._timer.stop()
            self._timer = None
    
    def _update_elapsed(self) -> None:
        """Update elapsed seconds while running."""
        if self._app.is_running and self._conversation_start_time is not None:
            import time
            new_elapsed = int(time.time() - self._conversation_start_time)
            if new_elapsed != self._app.elapsed_seconds:
                self._app.elapsed_seconds = new_elapsed
    
    # ---- State Update Methods ----
    # These methods are thread-safe and can be called from background threads.
    
    def set_running(self, is_running: bool) -> None:
        """Set the running state. Thread-safe."""
        import time
        
        def do_update():
            old_running = self._app.is_running
            self._app.is_running = is_running
            
            if is_running and not old_running:
                # Started running
                self._conversation_start_time = time.time()
                self._app.elapsed_seconds = 0
                self._app.post_message(ConversationStarted())
            elif not is_running and old_running:
                # Stopped running
                self._conversation_start_time = None
                self._app.post_message(ConversationFinished())
        
        self._schedule_on_main_thread(do_update)
    
    def set_confirmation_mode(self, is_active: bool) -> None:
        """Set confirmation mode state. Thread-safe."""
        self._is_confirmation_mode = is_active
    
    def set_cloud_ready(self, ready: bool = True) -> None:
        """Set cloud workspace ready state. Thread-safe."""
        self._cloud_ready = ready
    
    def set_pending_actions(self, count: int) -> None:
        """Set the number of pending actions. Thread-safe."""
        self._pending_actions_count = count
    
    def update_metrics(
        self,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
        cache_hit_rate: str | None = None,
        last_request_input_tokens: int | None = None,
        context_window: int | None = None,
        accumulated_cost: float | None = None,
    ) -> None:
        """Update conversation metrics. Thread-safe."""
        def do_update():
            if input_tokens is not None:
                self._app.input_tokens = input_tokens
            if output_tokens is not None:
                self._app.output_tokens = output_tokens
            if cache_hit_rate is not None:
                self._app.cache_hit_rate = cache_hit_rate
            if last_request_input_tokens is not None:
                self._app.last_request_input_tokens = last_request_input_tokens
            if context_window is not None:
                self._app.context_window = context_window
            if accumulated_cost is not None:
                self._app.accumulated_cost = accumulated_cost
        
        self._schedule_on_main_thread(do_update)
    
    def _schedule_on_main_thread(self, callback) -> None:
        """Schedule a callback on the main thread. Thread-safe."""
        try:
            # Try to call directly if we're in main thread
            from textual._context import active_app
            _ = active_app.get()
            callback()
        except LookupError:
            # We're in a background thread, schedule on main thread
            self._app.call_from_thread(callback)
    
    def get_snapshot(self) -> ConversationStateSnapshot:
        """Get an immutable snapshot of current state."""
        return ConversationStateSnapshot(
            is_running=self._app.is_running,
            is_confirmation_mode=self._is_confirmation_mode,
            cloud_ready=self._cloud_ready,
            cloud_mode=self._cloud_mode,
            elapsed_seconds=self._app.elapsed_seconds,
            pending_actions_count=self._pending_actions_count,
            metrics=ConversationMetrics(
                input_tokens=self._app.input_tokens,
                output_tokens=self._app.output_tokens,
                cache_hit_rate=self._app.cache_hit_rate,
                last_request_input_tokens=self._app.last_request_input_tokens,
                context_window=self._app.context_window,
                accumulated_cost=self._app.accumulated_cost,
            )
        )
    
    def reset(self) -> None:
        """Reset state for a new conversation."""
        def do_reset():
            self._app.is_running = False
            self._app.elapsed_seconds = 0
            self._pending_actions_count = 0
            self._app.input_tokens = 0
            self._app.output_tokens = 0
            self._app.cache_hit_rate = "N/A"
            self._app.last_request_input_tokens = 0
            self._app.context_window = 0
            self._app.accumulated_cost = 0.0
            self._conversation_start_time = None
        
        self._schedule_on_main_thread(do_reset)
