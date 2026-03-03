"""In-memory token-based session management."""

import secrets


class SessionManager:
    """Maps session tokens to user IDs."""

    def __init__(self):
        self._sessions: dict[str, int] = {}

    def create_session(self, user_id: int) -> str:
        """Create a new session token for the given user_id."""
        token = secrets.token_hex(32)
        self._sessions[token] = user_id
        return token

    def get_user_id(self, token: str) -> int | None:
        """Return the user_id associated with the token, or None."""
        return self._sessions.get(token)

    def remove_session(self, token: str) -> None:
        """Remove a session token."""
        self._sessions.pop(token, None)
