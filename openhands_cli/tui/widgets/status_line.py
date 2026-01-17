from __future__ import annotations

import os
import time
from typing import TYPE_CHECKING

from textual.reactive import var
from textual.timer import Timer
from textual.widgets import Static

from openhands_cli.locations import WORK_DIR
from openhands_cli.utils import abbreviate_number, format_cost


if TYPE_CHECKING:
    from openhands_cli.tui.textual_app import OpenHandsApp


class WorkingStatusLine(Static):
    """Status line showing conversation timer and working indicator (above input).
    
    This widget uses Textual's reactive system for state management.
    Bind to StateManager properties using data_bind() for automatic updates:
    
        status_line.data_bind(
            is_running=state_manager.is_running,
            elapsed_seconds=state_manager.elapsed_seconds
        )
    """

    DEFAULT_CSS = """
    #working_status_line {
        height: 1;
        background: $background;
        color: $secondary;
        padding: 0 1;
    }
    """
    
    # Reactive properties that can be bound to StateManager
    is_running: var[bool] = var(False)
    elapsed_seconds: var[int] = var(0)

    def __init__(self, app: "OpenHandsApp | None" = None, **kwargs) -> None:
        super().__init__("", id="working_status_line", markup=False, **kwargs)
        self._timer: Timer | None = None
        self._working_frame: int = 0
        # Keep app reference for backward compatibility during migration
        self.main_app = app

    def on_mount(self) -> None:
        """Initialize the working status line and start animation timer."""
        self._update_text()
        # Start animation timer for spinner (runs continuously but only animates when working)
        self._timer = self.set_interval(0.1, self._on_tick)
        
        # Backward compatibility: subscribe to signal if app provided
        if self.main_app is not None:
            self.main_app.conversation_running_signal.subscribe(
                self, self._on_legacy_state_changed
            )

    def on_unmount(self) -> None:
        """Stop timer when widget is removed."""
        if self._timer:
            self._timer.stop()
            self._timer = None

    def _on_legacy_state_changed(self, is_running: bool) -> None:
        """Legacy callback for signal-based state updates.
        
        This maintains backward compatibility during migration.
        New code should use data_bind() with StateManager instead.
        """
        self.is_running = is_running
        if not is_running:
            self.elapsed_seconds = 0

    # ----- Reactive Watchers -----
    
    def watch_is_running(self, is_running: bool) -> None:
        """React to running state changes."""
        self._update_text()
    
    def watch_elapsed_seconds(self, elapsed: int) -> None:
        """React to elapsed time changes."""
        self._update_text()

    # ----- Internal helpers -----

    def _on_tick(self) -> None:
        """Periodic update for animation."""
        if self.is_running:
            self._working_frame = (self._working_frame + 1) % 8
            self._update_text()

    def _get_working_text(self) -> str:
        """Return working status text if conversation is running."""
        if not self.is_running:
            return ""

        # Add working indicator with Braille spinner animation
        frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧"]
        working_indicator = f"{frames[self._working_frame % len(frames)]} Working"

        return f"{working_indicator} ({self.elapsed_seconds}s • ESC: pause)"

    def _update_text(self) -> None:
        """Rebuild the working status text."""
        working_text = self._get_working_text()
        self.update(working_text if working_text else " ")


class InfoStatusLine(Static):
    """Status line showing work directory, input mode, and conversation metrics.
    
    This widget uses Textual's reactive system for state management.
    Bind to StateManager properties using data_bind() for automatic updates:
    
        info_line.data_bind(
            is_running=state_manager.is_running,
            is_multiline_mode=state_manager.is_multiline_mode,
            input_tokens=state_manager.input_tokens,
            output_tokens=state_manager.output_tokens,
            ...
        )
    """

    DEFAULT_CSS = """
    #info_status_line {
        height: 1;
        background: $background;
        color: $secondary;
        padding: 0 1;
    }
    """
    
    # Reactive properties that can be bound to StateManager
    is_running: var[bool] = var(False)
    is_multiline_mode: var[bool] = var(False)
    input_tokens: var[int] = var(0)
    output_tokens: var[int] = var(0)
    cache_hit_rate: var[str] = var("N/A")
    last_request_input_tokens: var[int] = var(0)
    context_window: var[int] = var(0)
    accumulated_cost: var[float] = var(0.0)

    def __init__(self, app: "OpenHandsApp | None" = None, **kwargs) -> None:
        super().__init__("", id="info_status_line", markup=True, **kwargs)
        # Keep app reference for backward compatibility during migration
        self.main_app = app
        self.work_dir_display = self._get_work_dir_display()
        self._metrics_update_timer: Timer | None = None

    def on_mount(self) -> None:
        """Initialize the info status line."""
        self._update_text()
        
        # Backward compatibility: subscribe to signals if app provided
        if self.main_app is not None:
            self.main_app.input_field.multiline_mode_status.subscribe(
                self, self._on_legacy_multiline_mode
            )
            self.main_app.conversation_running_signal.subscribe(
                self, self._on_legacy_state_changed
            )

    def on_unmount(self) -> None:
        """Stop timer when widget is removed."""
        if self._metrics_update_timer:
            self._metrics_update_timer.stop()
            self._metrics_update_timer = None

    def on_resize(self) -> None:
        """Recalculate layout when widget is resized."""
        self._update_text()

    def _on_legacy_state_changed(self, is_running: bool) -> None:
        """Legacy callback for signal-based state updates.
        
        This maintains backward compatibility during migration.
        New code should use data_bind() with StateManager instead.
        """
        self.is_running = is_running
        if is_running:
            # Start periodic metrics updates while conversation is running
            if self._metrics_update_timer:
                self._metrics_update_timer.stop()
            self._metrics_update_timer = self.set_interval(1.0, self._poll_metrics)
        else:
            # Stop timer and do final metrics update
            if self._metrics_update_timer:
                self._metrics_update_timer.stop()
                self._metrics_update_timer = None
            self._poll_metrics()

    def _poll_metrics(self) -> None:
        """Poll conversation metrics from the runner (legacy method).
        
        This is used for backward compatibility. With the new StateManager,
        metrics are pushed via reactive properties instead of polled.
        """
        if self.main_app and self.main_app.conversation_runner:
            visualizer = self.main_app.conversation_runner.visualizer
            stats = visualizer.conversation_stats
            if stats:
                combined_metrics = stats.get_combined_metrics()
                if combined_metrics:
                    self.accumulated_cost = combined_metrics.accumulated_cost or 0.0
                    usage = combined_metrics.accumulated_token_usage
                    if usage:
                        self.input_tokens = usage.prompt_tokens or 0
                        self.output_tokens = usage.completion_tokens or 0
                        self.context_window = usage.context_window or 0
                        # Calculate cache hit rate
                        prompt = usage.prompt_tokens or 0
                        cache_read = usage.cache_read_tokens or 0
                        if prompt > 0:
                            self.cache_hit_rate = f"{(cache_read / prompt * 100):.0f}%"
                        else:
                            self.cache_hit_rate = "N/A"
                    # Get last request's input tokens (current context usage)
                    token_usages = combined_metrics.token_usages
                    if token_usages:
                        self.last_request_input_tokens = (
                            token_usages[-1].prompt_tokens or 0
                        )
                    else:
                        self.last_request_input_tokens = 0
        self._update_text()

    def _on_legacy_multiline_mode(self, is_multiline: bool) -> None:
        """Legacy callback for multiline mode signal."""
        self.is_multiline_mode = is_multiline

    # ----- Reactive Watchers -----
    
    def watch_is_multiline_mode(self, is_multiline: bool) -> None:
        """React to multiline mode changes."""
        self._update_text()
    
    def watch_input_tokens(self, value: int) -> None:
        """React to input token changes."""
        self._update_text()
    
    def watch_output_tokens(self, value: int) -> None:
        """React to output token changes."""
        self._update_text()
    
    def watch_accumulated_cost(self, value: float) -> None:
        """React to cost changes."""
        self._update_text()
    
    def watch_cache_hit_rate(self, value: str) -> None:
        """React to cache hit rate changes."""
        self._update_text()
    
    def watch_last_request_input_tokens(self, value: int) -> None:
        """React to context usage changes."""
        self._update_text()
    
    def watch_context_window(self, value: int) -> None:
        """React to context window changes."""
        self._update_text()

    # ----- Internal helpers -----

    @property
    def mode_indicator(self) -> str:
        """Get the mode indicator text based on current mode."""
        if self.is_multiline_mode:
            return "\\[Multi-line: Ctrl+J to submit • Ctrl+X for custom editor]"
        return "\\[Ctrl+L for multi-line • Ctrl+X for custom editor]"

    def _get_work_dir_display(self) -> str:
        """Get the work directory display string with tilde-shortening."""
        work_dir = WORK_DIR
        home = os.path.expanduser("~")
        if work_dir.startswith(home):
            work_dir = work_dir.replace(home, "~", 1)
        return work_dir

    def _format_metrics_display(self) -> str:
        """Format the conversation metrics for display.

        Shows: context (current / total) • cost (input tokens • output tokens • cache)
        """
        # Context display: show current context usage / total context window
        if self.last_request_input_tokens > 0:
            ctx_current = abbreviate_number(self.last_request_input_tokens)
            if self.context_window > 0:
                ctx_total = abbreviate_number(self.context_window)
                ctx_display = f"ctx {ctx_current} / {ctx_total}"
            else:
                ctx_display = f"ctx {ctx_current}"
        else:
            ctx_display = "ctx N/A"

        cost_display = f"$ {format_cost(self.accumulated_cost)}"
        token_details = (
            f"↑ {abbreviate_number(self.input_tokens)} "
            f"↓ {abbreviate_number(self.output_tokens)} "
            f"cache {self.cache_hit_rate}"
        )
        return f"{ctx_display} • {cost_display} ({token_details})"

    def _update_text(self) -> None:
        """Rebuild the info status text with metrics right-aligned in grey."""
        left_part = f"{self.mode_indicator} • {self.work_dir_display}"
        metrics_display = self._format_metrics_display()

        # Calculate available width for spacing (account for padding of 2 chars)
        try:
            total_width = self.size.width - 2
        except Exception:
            total_width = 80  # Fallback width

        # Calculate spacing needed to right-align metrics
        left_len = len(left_part)
        right_len = len(metrics_display)
        spacing = max(1, total_width - left_len - right_len)

        # Build status text with grey metrics on the right
        status_text = f"{left_part}{' ' * spacing}[grey50]{metrics_display}[/grey50]"
        self.update(status_text)
