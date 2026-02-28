"""HTTP client adapter for the budget planner frontend.

Implements the same handle(dict) interface as RequestHandler but
dispatches each action to the FastAPI backend over HTTP.
"""

import logging

import requests
from dotenv import load_dotenv
import os

load_dotenv()

logger = logging.getLogger(__name__)

_DEFAULT_BASE_URL = os.getenv("BACKEND_URL")


class HttpRequestHandler:
    """Translates handle(dict) calls into HTTP requests to the FastAPI backend."""

    def __init__(self, base_url: str = _DEFAULT_BASE_URL):
        self._base = base_url.rstrip("/")
        self._session = requests.Session()

    #  Public entry point (mirrors RequestHandler.handle)
    def handle(self, request: dict) -> dict:
        action = request.get("action", "")
        data = request.get("data", {})
        try:
            return self._dispatch(action, data)
        except requests.ConnectionError:
            return {
                "status": "error",
                "message": (
                    f"Cannot connect to the backend server at {self._base}. "
                    "Make sure it is running."
                ),
            }
        except Exception as exc:
            logger.exception("Unexpected error calling backend for action=%s", action)
            return {"status": "error", "message": str(exc)}

    #  Low-level HTTP helpers
    def _get(self, path: str, params: dict = None) -> dict:
        resp = self._session.get(f"{self._base}{path}", params=params or {})
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, body: dict = None) -> dict:
        resp = self._session.post(f"{self._base}{path}", json=body or {})
        resp.raise_for_status()
        return resp.json()

    def _put(self, path: str, body: dict = None) -> dict:
        resp = self._session.put(f"{self._base}{path}", json=body or {})
        resp.raise_for_status()
        return resp.json()

    def _delete(self, path: str, params: dict = None) -> dict:
        resp = self._session.delete(f"{self._base}{path}", params=params or {})
        resp.raise_for_status()
        return resp.json()

    #  Action -> HTTP routing
    def _dispatch(self, action: str, data: dict) -> dict:
        # Dashboard / general
        if action == "get_dashboard":
            return self._get("/dashboard")
        if action == "get_help":
            return self._get("/help")

        # Categories
        if action == "get_categories":
            return self._get(
                "/categories",
                params={"transaction_type": data.get("transaction_type", "expense")},
            )

        # Transactions
        if action == "get_transaction":
            return self._get(f"/transactions/{data['index']}")
        if action == "add_transaction":
            return self._post("/transactions", body=data)
        if action == "edit_transaction":
            index = data["index"]
            body = {k: v for k, v in data.items() if k != "index"}
            return self._put(f"/transactions/{index}", body=body)
        if action == "delete_transaction":
            return self._delete(f"/transactions/{data['index']}")

        # Transfer
        if action == "get_transfer_context":
            return self._get("/transfer")
        if action == "transfer":
            return self._post("/transfer", body=data)

        # Sorting
        if action == "get_sorting_options":
            return self._get("/sorting")
        if action == "set_sorting":
            return self._post("/sorting", body=data)
        if action == "get_wallet_sorting_options":
            return self._get("/sorting/wallets")
        if action == "set_wallet_sorting":
            return self._post("/sorting/wallets", body=data)

        # Filters
        if action == "get_active_filters":
            return self._get("/filters")
        if action == "add_filter":
            return self._post("/filters", body=data)
        if action == "remove_filter":
            return self._delete(f"/filters/{data['filter_index']}")
        if action == "clear_filters":
            return self._delete("/filters")

        # Percentages
        if action == "get_percentages":
            return self._get("/percentages")

        # Wallets
        if action == "get_wallets":
            return self._get("/wallets")
        if action == "get_wallet_detail":
            return self._get(f"/wallets/{data['name']}")
        if action == "add_wallet":
            return self._post("/wallets", body=data)
        if action == "edit_wallet":
            name = data["name"]
            body = {k: v for k, v in data.items() if k != "name"}
            return self._put(f"/wallets/{name}", body=body)
        if action == "delete_wallet":
            return self._delete(f"/wallets/{data['name']}")
        if action == "switch_wallet":
            return self._post("/wallets/switch", body=data)

        # Recurring
        if action == "process_recurring":
            return self._post("/recurring/process")
        if action == "get_recurring_list":
            return self._get("/recurring")
        if action == "get_recurring_detail":
            return self._get(f"/recurring/{data['index']}")
        if action == "add_recurring":
            return self._post("/recurring", body=data)
        if action == "edit_recurring":
            index = data["index"]
            body = {k: v for k, v in data.items() if k != "index"}
            return self._put(f"/recurring/{index}", body=body)
        if action == "delete_recurring":
            return self._delete(
                f"/recurring/{data['index']}",
                params={"delete_option": data.get("delete_option", 1)},
            )

        return {"status": "error", "message": f"Unknown action: {action}"}
