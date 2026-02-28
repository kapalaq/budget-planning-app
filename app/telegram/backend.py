"""Async HTTP client for communicating with the FastAPI backend."""

import logging

import aiohttp

from telegram.config import BACKEND_URL

logger = logging.getLogger(__name__)


class Backend:
    """Async adapter matching the handle(dict) interface used by the CLI."""

    def __init__(self, base_url: str = BACKEND_URL):
        self._base = base_url.rstrip("/")
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def handle(self, request: dict) -> dict:
        action = request.get("action", "")
        data = request.get("data", {})
        try:
            return await self._dispatch(action, data)
        except aiohttp.ClientError:
            return {
                "status": "error",
                "message": (
                    f"Cannot connect to backend at {self._base}. "
                    "Make sure it is running."
                ),
            }
        except Exception as exc:
            logger.exception("Backend error for action=%s", action)
            return {"status": "error", "message": str(exc)}

    async def _get(self, path: str, params: dict | None = None) -> dict:
        session = await self._get_session()
        async with session.get(f"{self._base}{path}", params=params or {}) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def _post(self, path: str, body: dict | None = None) -> dict:
        session = await self._get_session()
        async with session.post(f"{self._base}{path}", json=body or {}) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def _put(self, path: str, body: dict | None = None) -> dict:
        session = await self._get_session()
        async with session.put(f"{self._base}{path}", json=body or {}) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def _delete(self, path: str, params: dict | None = None) -> dict:
        session = await self._get_session()
        async with session.delete(f"{self._base}{path}", params=params or {}) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def _dispatch(self, action: str, data: dict) -> dict:
        # Dashboard / general
        if action == "get_dashboard":
            return await self._get("/dashboard")
        if action == "get_help":
            return await self._get("/help")

        # Categories
        if action == "get_categories":
            return await self._get(
                "/categories",
                params={"transaction_type": data.get("transaction_type", "expense")},
            )

        # Transactions
        if action == "get_transaction":
            return await self._get(f"/transactions/{data['index']}")
        if action == "add_transaction":
            return await self._post("/transactions", body=data)
        if action == "edit_transaction":
            index = data["index"]
            body = {k: v for k, v in data.items() if k != "index"}
            return await self._put(f"/transactions/{index}", body=body)
        if action == "delete_transaction":
            return await self._delete(f"/transactions/{data['index']}")

        # Transfer
        if action == "get_transfer_context":
            return await self._get("/transfer")
        if action == "transfer":
            return await self._post("/transfer", body=data)

        # Sorting
        if action == "get_sorting_options":
            return await self._get("/sorting")
        if action == "set_sorting":
            return await self._post("/sorting", body=data)
        if action == "get_wallet_sorting_options":
            return await self._get("/sorting/wallets")
        if action == "set_wallet_sorting":
            return await self._post("/sorting/wallets", body=data)

        # Filters
        if action == "get_active_filters":
            return await self._get("/filters")
        if action == "add_filter":
            return await self._post("/filters", body=data)
        if action == "remove_filter":
            return await self._delete(f"/filters/{data['filter_index']}")
        if action == "clear_filters":
            return await self._delete("/filters")

        # Percentages
        if action == "get_percentages":
            return await self._get("/percentages")

        # Wallets
        if action == "get_wallets":
            return await self._get("/wallets")
        if action == "get_wallet_detail":
            return await self._get(f"/wallets/{data['name']}")
        if action == "add_wallet":
            return await self._post("/wallets", body=data)
        if action == "edit_wallet":
            name = data["name"]
            body = {k: v for k, v in data.items() if k != "name"}
            return await self._put(f"/wallets/{name}", body=body)
        if action == "delete_wallet":
            return await self._delete(f"/wallets/{data['name']}")
        if action == "switch_wallet":
            return await self._post("/wallets/switch", body=data)

        # Recurring
        if action == "process_recurring":
            return await self._post("/recurring/process")
        if action == "get_recurring_list":
            return await self._get("/recurring")
        if action == "get_recurring_detail":
            return await self._get(f"/recurring/{data['index']}")
        if action == "add_recurring":
            return await self._post("/recurring", body=data)
        if action == "edit_recurring":
            index = data["index"]
            body = {k: v for k, v in data.items() if k != "index"}
            return await self._put(f"/recurring/{index}", body=body)
        if action == "delete_recurring":
            return await self._delete(
                f"/recurring/{data['index']}",
                params={"delete_option": data.get("delete_option", 1)},
            )

        return {"status": "error", "message": f"Unknown action: {action}"}


backend = Backend()
