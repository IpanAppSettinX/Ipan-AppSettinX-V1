from __future__ import annotations

import pytest

from ipan_optimizer.game.session import GameSessionController


def test_dry_run_game_session_restores() -> None:
    controller = GameSessionController(dry_run=True)
    session = controller.start("gaming-balanced", "game-1")
    assert session.state == "DRY_RUN_ACTIVE"
    assert controller.stop(session.session_id).state == "RESTORED"


def test_real_session_controller_is_release_gated() -> None:
    with pytest.raises(RuntimeError, match="belum diaktifkan"):
        GameSessionController(dry_run=False)
