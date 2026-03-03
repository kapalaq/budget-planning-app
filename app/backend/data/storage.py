"""JSON file storage keyed by user_id."""

import json
import logging
import os

logger = logging.getLogger(__name__)


class JsonStorage:
    """Reads and writes per-user JSON data files."""

    def __init__(self, data_dir: str):
        self._data_dir = data_dir
        os.makedirs(self._data_dir, exist_ok=True)

    def _path(self, user_id: int) -> str:
        return os.path.join(self._data_dir, f"user_{user_id}.json")

    def load(self, user_id: int) -> dict:
        path = self._path(user_id)
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save(self, user_id: int, data: dict) -> None:
        path = self._path(user_id)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            logger.error("Failed to save data for user %s", user_id, exc_info=e)
