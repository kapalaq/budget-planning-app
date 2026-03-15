"""PostgreSQL-based user management."""

import logging

import psycopg2.errors

logger = logging.getLogger(__name__)


class UserStore:
    """Manages users via a PostgreSQL database."""

    def __init__(self, conn):
        """Wrap an existing psycopg2 connection and ensure the users table exists."""
        self._conn = conn
        self._ensure_table()
        logger.info("UserStore initialised")

    def _ensure_table(self):
        """Create the users table if it doesn't exist."""
        with self._conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id     SERIAL PRIMARY KEY,
                    login       VARCHAR(255) UNIQUE NOT NULL,
                    password    VARCHAR(255) NOT NULL,
                    telegram_id VARCHAR(255) DEFAULT ''
                );
                """)
            # Add language column if missing (migration)
            cur.execute("""
                DO $$
                BEGIN
                    ALTER TABLE users ADD COLUMN language VARCHAR(10) DEFAULT 'en-US';
                EXCEPTION
                    WHEN duplicate_column THEN NULL;
                END $$;
                """)

    # ── Authentication ───────────────────────────────────────────────

    def authenticate(self, login: str, password: str) -> int | None:
        """Return user_id if credentials match, else None."""
        with self._conn.cursor() as cur:
            cur.execute(
                "SELECT user_id FROM users WHERE login = %s AND password = %s",
                (login, password),
            )
            row = cur.fetchone()
        return row[0] if row else None

    def register(self, login: str, password: str, telegram_id: str = "") -> int | None:
        """Create a new user. Returns user_id, or None if login already taken."""
        try:
            with self._conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO users (login, password, telegram_id) VALUES (%s, %s, %s) RETURNING user_id",
                    (login, password, telegram_id),
                )
                row = cur.fetchone()
            return row[0]
        except psycopg2.errors.UniqueViolation:
            return None

    # ── Telegram ID management ───────────────────────────────────────

    def find_by_telegram_id(self, telegram_id: str) -> int | None:
        """Return user_id for the given telegram_id, or None."""
        with self._conn.cursor() as cur:
            cur.execute(
                "SELECT user_id FROM users WHERE telegram_id = %s",
                (telegram_id,),
            )
            row = cur.fetchone()
        return row[0] if row else None

    def authenticate_by_telegram_id(self, telegram_id: str) -> int | None:
        """Return user_id for the given telegram_id, or None if not linked."""
        return self.find_by_telegram_id(telegram_id)

    def update_telegram_id(self, user_id: int, telegram_id: str) -> bool:
        """Link a telegram_id to an existing user.

        Enforces one-telegram-per-user: clears telegram_id from any other
        user that currently has this telegram_id.
        """
        with self._conn.cursor() as cur:
            if telegram_id:
                cur.execute(
                    "UPDATE users SET telegram_id = '' WHERE telegram_id = %s AND user_id != %s",
                    (telegram_id, user_id),
                )
            cur.execute(
                "UPDATE users SET telegram_id = %s WHERE user_id = %s",
                (telegram_id, user_id),
            )
            return cur.rowcount > 0

    def clear_telegram_id(self, telegram_id: str) -> bool:
        """Unlink a telegram_id from whichever user has it. Returns True if found."""
        with self._conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET telegram_id = '' WHERE telegram_id = %s",
                (telegram_id,),
            )
            return cur.rowcount > 0

    # ── Language preference ──────────────────────────────────────────

    def get_language(self, user_id: int) -> str:
        """Return the user's preferred language code, defaulting to 'en-US'."""
        with self._conn.cursor() as cur:
            cur.execute(
                "SELECT language FROM users WHERE user_id = %s",
                (user_id,),
            )
            row = cur.fetchone()
        return row[0] if row and row[0] else "en-US"

    def set_language(self, user_id: int, language: str) -> bool:
        """Set the user's preferred language. Returns True if updated."""
        with self._conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET language = %s WHERE user_id = %s",
                (language, user_id),
            )
            return cur.rowcount > 0
