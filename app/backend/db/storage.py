"""MongoDB-backed storage keyed by user_id."""

import logging

from pymongo.collection import Collection
from pymongo.database import Database

logger = logging.getLogger(__name__)


class MongoStorage:
    """Reads and writes per-user wallet data in MongoDB."""

    def __init__(self, db: Database):
        self._col: Collection = db["user_data"]
        self._col.create_index("user_id", unique=True)

    def load(self, key: int | str) -> dict:
        doc = self._col.find_one({"user_id": key})
        if doc is None:
            return {}
        doc.pop("_id", None)
        doc.pop("user_id", None)
        return doc

    def save(self, key: int | str, data: dict) -> None:
        try:
            self._col.replace_one(
                {"user_id": key},
                {"user_id": key, **data},
                upsert=True,
            )
        except Exception as e:
            logger.error("Failed to save data for key %s", key, exc_info=e)
