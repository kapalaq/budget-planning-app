"""CSV-based user management."""

import csv
import logging
import os

logger = logging.getLogger(__name__)

# To enable password hashing, uncomment the following lines and
# replace plain-text comparisons with hashed ones:
# import hashlib
# def _hash(password: str) -> str:
#     return hashlib.sha256(password.encode()).hexdigest()


class UserStore:
    """Manages users via a CSV file (user_id, login, password, telegram_id)."""

    _FIELDNAMES = ["user_id", "login", "password", "telegram_id"]

    def __init__(self, csv_path: str):
        self._path = csv_path
        self._users: list[dict] = []
        self._next_id: int = 1
        self._load()

    def _load(self):
        if not os.path.exists(self._path):
            self._users = []
            self._next_id = 1
            return
        with open(self._path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f, fieldnames=self._FIELDNAMES)
            self._users = []
            for row in reader:
                row["user_id"] = int(row["user_id"])
                self._users.append(row)
        if self._users:
            self._next_id = max(u["user_id"] for u in self._users) + 1
        else:
            self._next_id = 1

    def _save(self):
        with open(self._path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=self._FIELDNAMES)
            writer.writerows(self._users)

    def authenticate(self, login: str, password: str) -> int | None:
        """Return user_id if credentials match, else None."""
        # For hashed passwords: compare _hash(password) instead
        for user in self._users:
            if user["login"] == login and user["password"] == password:
                return user["user_id"]
        return None

    def register(self, login: str, password: str, telegram_id: str = "") -> int | None:
        """Create a new user. Returns user_id, or None if login already taken."""
        for user in self._users:
            if user["login"] == login:
                return None
        user_id = self._next_id
        self._next_id += 1
        # For hashed passwords: store _hash(password) instead
        self._users.append(
            {
                "user_id": user_id,
                "login": login,
                "password": password,
                "telegram_id": telegram_id,
            }
        )
        self._save()
        return user_id

    def find_by_telegram_id(self, telegram_id: str) -> int | None:
        """Return user_id for the given telegram_id, or None."""
        for user in self._users:
            if user["telegram_id"] == telegram_id:
                return user["user_id"]
        return None

    def authenticate_by_telegram_id(self, telegram_id: str) -> int | None:
        """Return user_id for the given telegram_id, or None if not linked."""
        return self.find_by_telegram_id(telegram_id)

    def update_telegram_id(self, user_id: int, telegram_id: str) -> bool:
        """Link a telegram_id to an existing user. Returns True on success."""
        for user in self._users:
            if user["user_id"] == user_id:
                user["telegram_id"] = telegram_id
                self._save()
                return True
        return False
