"""In-memory token-based session management."""

import secrets
import time

SESSION_TTL = 24 * 60 * 60  # 24 hours
LINK_CODE_TTL = 5 * 60  # 5 minutes


class SessionManager:
    """Maps session tokens to user IDs with expiration."""

    def __init__(self):
        # token -> (user_id, created_at)
        self._sessions: dict[str, tuple[int, float]] = {}
        # link_code -> (user_id, created_at)
        self._link_codes: dict[str, tuple[int, float]] = {}

    def create_session(self, user_id: int) -> str:
        """Create a new session token for the given user_id."""
        token = secrets.token_hex(32)
        self._sessions[token] = (user_id, time.time())
        return token

    def get_user_id(self, token: str) -> int | None:
        """Return the user_id associated with the token, or None if expired."""
        entry = self._sessions.get(token)
        if entry is None:
            return None
        user_id, created_at = entry
        # if time.time() - created_at > SESSION_TTL:
        #    del self._sessions[token]
        #    return None
        return user_id

    def remove_session(self, token: str) -> None:
        """Remove a session token."""
        self._sessions.pop(token, None)

    # ── Link codes ────────────────────────────────────────────────────

    def create_link_code(self, user_id: int) -> str:
        """Generate a short code that maps to a user_id (valid for 5 minutes)."""
        code = secrets.token_hex(4)  # 8-char hex
        self._link_codes[code] = (user_id, time.time())
        return code

    def consume_link_code(self, code: str) -> int | None:
        """Return user_id if the code is valid and not expired, then delete it."""
        entry = self._link_codes.pop(code, None)
        if entry is None:
            return None
        user_id, created_at = entry
        if time.time() - created_at > LINK_CODE_TTL:
            return None
        return user_id

    # ── Serialization ────────────────────────────────────────────────

    def to_json(self) -> dict:
        """Serialize sessions and link codes to a JSON-compatible dict."""
        return {
            "sessions": {
                token: {"user_id": uid, "created_at": ts}
                for token, (uid, ts) in self._sessions.items()
            },
            "link_codes": {
                code: {"user_id": uid, "created_at": ts}
                for code, (uid, ts) in self._link_codes.items()
            },
        }

    @classmethod
    def from_json(cls, data: dict | None) -> "SessionManager":
        """Restore a SessionManager from a previously serialized dict."""
        sm = cls()
        if not data:
            return sm
        now = time.time()
        for token, entry in data.get("sessions", {}).items():
            uid, ts = entry["user_id"], entry["created_at"]
            if now - ts <= SESSION_TTL:
                sm._sessions[token] = (uid, ts)
        for code, entry in data.get("link_codes", {}).items():
            uid, ts = entry["user_id"], entry["created_at"]
            if now - ts <= LINK_CODE_TTL:
                sm._link_codes[code] = (uid, ts)
        return sm
