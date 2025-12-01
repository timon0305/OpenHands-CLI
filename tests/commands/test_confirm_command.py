#!/usr/bin/env python3

from unittest.mock import MagicMock, patch

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
    # Arrange: pick starting runner & prepare the target conversation
    runner = ConversationRunner(make_conv(enabled=start_enabled))
    target_conv = make_conv(enabled=expected_enabled)

    with patch(
        "openhands_cli.runner.setup_conversation", return_value=target_conv
    ) as mock_setup:
        # Act
        runner.toggle_confirmation_mode()

        # Assert state
        assert runner.is_confirmation_mode_active is expected_enabled
        assert runner.conversation is target_conv

        # Assert setup called with conversation ID + correct confirmation policy
        mock_setup.assert_called_once()
        call_args = mock_setup.call_args
        assert call_args.args[0] == CONV_ID
        assert isinstance(call_args.kwargs["confirmation_policy"], expected_policy_cls)

        # Policy is set inside setup_conversation, not called explicitly in toggle
        target_conv.set_confirmation_policy.assert_not_called()


# ---------- Conversation ID is preserved across multiple toggles ----------
def test_maintains_conversation_id_across_toggles(runner_disabled: ConversationRunner):
    enabled_conv = make_conv(enabled=True)
    disabled_conv = make_conv(enabled=False)

    with patch("openhands_cli.runner.setup_conversation") as mock_setup:
        mock_setup.side_effect = [enabled_conv, disabled_conv]

        # Toggle on (disabled -> enabled uses AlwaysConfirm),
        # then off (enabled -> disabled uses NeverConfirm)
        runner_disabled.toggle_confirmation_mode()
        runner_disabled.toggle_confirmation_mode()

        assert runner_disabled.conversation.id == CONV_ID
        # Verify correct conversation ID was passed and policy types
        assert mock_setup.call_count == 2
        call_1 = mock_setup.call_args_list[0]
        call_2 = mock_setup.call_args_list[1]
        assert call_1.args[0] == CONV_ID
        assert isinstance(call_1.kwargs["confirmation_policy"], AlwaysConfirm)
        assert call_2.args[0] == CONV_ID
        assert isinstance(call_2.kwargs["confirmation_policy"], NeverConfirm)


# ---------- Idempotency under rapid alternating toggles ----------
def test_rapid_alternating_toggles_produce_expected_states(
    runner_disabled: ConversationRunner,
):
    enabled_conv = make_conv(enabled=True)
    disabled_conv = make_conv(enabled=False)

    with patch("openhands_cli.runner.setup_conversation") as mock_setup:
        mock_setup.side_effect = [
            enabled_conv,
            disabled_conv,
            enabled_conv,
            disabled_conv,
        ]

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

        # Verify all 4 calls had correct conversation ID and policy types
        assert mock_setup.call_count == 4
        calls = mock_setup.call_args_list
        assert calls[0].args[0] == CONV_ID
        assert isinstance(calls[0].kwargs["confirmation_policy"], AlwaysConfirm)
        assert calls[1].args[0] == CONV_ID
        assert isinstance(calls[1].kwargs["confirmation_policy"], NeverConfirm)
        assert calls[2].args[0] == CONV_ID
        assert isinstance(calls[2].kwargs["confirmation_policy"], AlwaysConfirm)
        assert calls[3].args[0] == CONV_ID
        assert isinstance(calls[3].kwargs["confirmation_policy"], NeverConfirm)
