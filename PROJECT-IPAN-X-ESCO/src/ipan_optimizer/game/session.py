from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4


@dataclass
class GameSession:
    session_id: str
    profile_id: str
    executable_id: str
    state: str
    dry_run: bool


class GameSessionController:
    def __init__(self, *, dry_run: bool) -> None:
        if not dry_run:
            raise RuntimeError("Real game session controller belum diaktifkan.")
        self.sessions: dict[str, GameSession] = {}

    def start(self, profile_id: str, executable_id: str) -> GameSession:
        if not profile_id or not executable_id:
            raise ValueError("Profil dan executable wajib dipilih.")
        session = GameSession(
            session_id=str(uuid4()),
            profile_id=profile_id,
            executable_id=executable_id,
            state="DRY_RUN_ACTIVE",
            dry_run=True,
        )
        self.sessions[session.session_id] = session
        return session

    def stop(self, session_id: str) -> GameSession:
        session = self.sessions.get(session_id)
        if session is None:
            raise KeyError("Sesi game tidak ditemukan.")
        session.state = "RESTORED"
        return session
