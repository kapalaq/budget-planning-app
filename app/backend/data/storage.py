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

    def _path(self, key: int | str) -> str:
        return os.path.join(self._data_dir, f"user_{key}.json")

    def load(self, key: int | str) -> dict:
        path = self._path(key)
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save(self, key: int | str, data: dict) -> None:
        path = self._path(key)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            logger.error("Failed to save data for key %s", key, exc_info=e)
