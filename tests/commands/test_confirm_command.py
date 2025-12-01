#!/usr/bin/env python3

from unittest.mock import MagicMock

import pytest

from openhands.sdk.security.confirmation_policy import AlwaysConfirm, NeverConfirm
from openhands_cli.runner import ConversationRunner


CONV_ID = "test-conversation-id"


# ---------- Helpers ----------
def make_conv(enabled: bool) -> MagicMock:
    """Return a conversation mock in enabled/disabled confirmation mode."""
    m = MagicMock()
    m.id = CONV_ID
    m.agent.security_analyzer = MagicMock() if enabled else None
    m.confirmation_policy_active = enabled
    m.is_confirmation_mode_active = enabled

    # Track confirmation mode state and update when set_confirmation_policy is called
    def set_policy_side_effect(policy):
        # Update the mock's is_confirmation_mode_active based on policy type
        if isinstance(policy, NeverConfirm):
            m.is_confirmation_mode_active = False
        else:  # AlwaysConfirm or ConfirmRisky
            m.is_confirmation_mode_active = True

    m.set_confirmation_policy.side_effect = set_policy_side_effect
    return m


@pytest.fixture
def runner_disabled() -> ConversationRunner:
    """Runner starting with confirmation mode disabled."""
    return ConversationRunner(make_conv(enabled=False))


@pytest.fixture
def runner_enabled() -> ConversationRunner:
    """Runner starting with confirmation mode enabled."""
    return ConversationRunner(make_conv(enabled=True))


# ---------- Core toggle behavior (parametrized) ----------
@pytest.mark.parametrize(
    "start_enabled, expected_policy_cls, expected_enabled",
    [
        # disabled -> enable (use AlwaysConfirm policy)
        (False, AlwaysConfirm, True),
        # enabled -> disable (use NeverConfirm policy)
        (True, NeverConfirm, False),
    ],
)
def test_toggle_confirmation_mode_transitions(
    start_enabled, expected_policy_cls, expected_enabled
):
    # Arrange: pick starting runner
    runner = ConversationRunner(make_conv(enabled=start_enabled))

    # Act
    runner.toggle_confirmation_mode()

    # Assert state - confirmation mode should be toggled
    assert runner.is_confirmation_mode_active is expected_enabled

    # Assert set_confirmation_policy was called with correct policy
    runner.conversation.set_confirmation_policy.assert_called_once()  # type: ignore
    call_args = runner.conversation.set_confirmation_policy.call_args  # type: ignore
    assert isinstance(call_args.args[0], expected_policy_cls)


# ---------- Conversation ID is preserved across multiple toggles ----------
def test_maintains_conversation_id_across_toggles(runner_disabled: ConversationRunner):
    # Toggle on (disabled -> enabled uses AlwaysConfirm),
    # then off (enabled -> disabled uses NeverConfirm)
    runner_disabled.toggle_confirmation_mode()
    runner_disabled.toggle_confirmation_mode()

    # Conversation ID should remain the same
    assert runner_disabled.conversation.id == CONV_ID

    # Verify set_confirmation_policy was called twice with correct policy types
    assert runner_disabled.conversation.set_confirmation_policy.call_count == 2  # type: ignore
    call_1 = runner_disabled.conversation.set_confirmation_policy.call_args_list[0]  # type: ignore
    call_2 = runner_disabled.conversation.set_confirmation_policy.call_args_list[1]  # type: ignore
    assert isinstance(call_1.args[0], AlwaysConfirm)
    assert isinstance(call_2.args[0], NeverConfirm)


# ---------- Idempotency under rapid alternating toggles ----------
def test_rapid_alternating_toggles_produce_expected_states(
    runner_disabled: ConversationRunner,
):
    # Start disabled
    assert runner_disabled.is_confirmation_mode_active is False

    # Enable (AlwaysConfirm), Disable (NeverConfirm),
    # Enable (AlwaysConfirm), Disable (NeverConfirm)
    runner_disabled.toggle_confirmation_mode()
    assert runner_disabled.is_confirmation_mode_active is True

    runner_disabled.toggle_confirmation_mode()
    assert runner_disabled.is_confirmation_mode_active is False

    runner_disabled.toggle_confirmation_mode()
    assert runner_disabled.is_confirmation_mode_active is True

    runner_disabled.toggle_confirmation_mode()
    assert runner_disabled.is_confirmation_mode_active is False

    # Verify all 4 calls had correct policy types
    assert runner_disabled.conversation.set_confirmation_policy.call_count == 4  # type: ignore
    calls = runner_disabled.conversation.set_confirmation_policy.call_args_list  # type: ignore
    assert isinstance(calls[0].args[0], AlwaysConfirm)
    assert isinstance(calls[1].args[0], NeverConfirm)
    assert isinstance(calls[2].args[0], AlwaysConfirm)
    assert isinstance(calls[3].args[0], NeverConfirm)
