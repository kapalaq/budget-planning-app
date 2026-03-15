"""MongoDB-backed token-based session management."""

import logging
import secrets
from datetime import datetime, timezone

from pymongo.collection import Collection
from pymongo.database import Database

logger = logging.getLogger(__name__)

SESSION_TTL = 24 * 60 * 60  # 24 hours
LINK_CODE_TTL = 5 * 60  # 5 minutes


class SessionManager:
    """Maps session tokens to user IDs, backed by MongoDB with TTL indexes."""

    def __init__(self, db: Database):
        self._sessions: Collection = db["sessions"]
        self._link_codes: Collection = db["link_codes"]

        # Ensure TTL indexes (idempotent — no-op if already exists)
        self._sessions.create_index("created_at", expireAfterSeconds=SESSION_TTL)
        self._link_codes.create_index("created_at", expireAfterSeconds=LINK_CODE_TTL)
        # Unique index on token / code for fast lookups
        self._sessions.create_index("token", unique=True)
        self._link_codes.create_index("code", unique=True)

        logger.info("SessionManager initialised")

    # ── Sessions ─────────────────────────────────────────────────────

    def create_session(self, user_id: int) -> str:
        """Create a new session token for the given user_id."""
        token = secrets.token_hex(32)
        self._sessions.insert_one(
            {
                "token": token,
                "user_id": user_id,
                "created_at": datetime.now(timezone.utc),
            }
        )
        return token

    def get_user_id(self, token: str) -> int | None:
        """Return the user_id associated with the token, or None if expired/missing."""
        doc = self._sessions.find_one({"token": token})
        if doc is None:
            return None
        return doc["user_id"]

    def remove_session(self, token: str) -> None:
        """Remove a session token."""
        self._sessions.delete_one({"token": token})

    # ── Link codes ───────────────────────────────────────────────────

    def create_link_code(self, user_id: int) -> str:
        """Generate a short code that maps to a user_id (valid for 5 minutes)."""
        code = secrets.token_hex(4)  # 8-char hex
        self._link_codes.insert_one(
            {
                "code": code,
                "user_id": user_id,
                "created_at": datetime.now(timezone.utc),
            }
        )
        return code

    def consume_link_code(self, code: str) -> int | None:
        """Return user_id if the code is valid and not expired, then delete it."""
        doc = self._link_codes.find_one_and_delete({"code": code})
        if doc is None:
            return None
        return doc["user_id"]
