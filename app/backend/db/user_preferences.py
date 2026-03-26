"""MongoDB-backed user preferences (language, timezone, chart settings)."""

import logging

from pymongo.collection import Collection
from pymongo.database import Database

logger = logging.getLogger(__name__)

_DEFAULTS = {
    "language": "en-US",
    "timezone": 0,
    "hidden_chart_categories": {},
    "category_colors": {},
}


class UserPreferences:
    """Reads and writes per-user app preferences in MongoDB."""

    def __init__(self, db: Database):
        self._col: Collection = db["user_preferences"]
        self._col.create_index("user_id", unique=True)

    def _get_doc(self, user_id: int) -> dict:
        doc = self._col.find_one({"user_id": user_id})
        return doc or {}

    def _set_field(self, user_id: int, field: str, value):
        self._col.update_one(
            {"user_id": user_id},
            {"$set": {field: value}},
            upsert=True,
        )

    # ── Language ──────────────────────────────────────────────────────

    def get_language(self, user_id: int) -> str:
        doc = self._get_doc(user_id)
        return doc.get("language", _DEFAULTS["language"])

    def set_language(self, user_id: int, language: str) -> bool:
        self._set_field(user_id, "language", language)
        return True

    # ── Timezone ─────────────────────────────────────────────────────

    def get_timezone(self, user_id: int) -> int:
        doc = self._get_doc(user_id)
        val = doc.get("timezone", _DEFAULTS["timezone"])
        return val if isinstance(val, int) else _DEFAULTS["timezone"]

    def set_timezone(self, user_id: int, tz_offset: int) -> bool:
        self._set_field(user_id, "timezone", tz_offset)
        return True

    # ── Hidden chart categories ──────────────────────────────────────

    def get_hidden_chart_categories(self, user_id: int) -> dict:
        doc = self._get_doc(user_id)
        return doc.get(
            "hidden_chart_categories",
            _DEFAULTS["hidden_chart_categories"],
        )

    def set_hidden_chart_categories(self, user_id: int, data: dict) -> bool:
        self._set_field(user_id, "hidden_chart_categories", data)
        return True

    # ── Category colors ───────────────────────────────────────────────

    def get_category_colors(self, user_id: int) -> dict:
        doc = self._get_doc(user_id)
        return doc.get("category_colors", _DEFAULTS["category_colors"])

    def set_category_colors(self, user_id: int, data: dict) -> bool:
        self._set_field(user_id, "category_colors", data)
        return True
