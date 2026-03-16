"""Async HTTP client for communicating with the FastAPI backend."""

import contextvars
import logging

import aiohttp
from telegram.config import BACKEND_URL

logger = logging.getLogger(__name__)

# Context variable holding the auth token for the current request.
# Set by the auth middleware in bot.py before each handler runs.
_current_token: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "_current_token", default=None
)

# Context variable holding the user's language for the current request.
_current_lang: contextvars.ContextVar[str] = contextvars.ContextVar(
    "_current_lang", default="en-US"
)


def get_lang() -> str:
    """Return the current user's language code."""
    return _current_lang.get()


class Backend:
    """Async adapter matching the handle(dict) interface used by the CLI."""

    def __init__(self, base_url: str = BACKEND_URL):
        self._base = base_url.rstrip("/")
        self._session: aiohttp.ClientSession | None = None
        # Cache: telegram_user_id -> backend auth token
        self._tokens: dict[int, str] = {}
        # Cache: telegram_user_id -> language code
        self._langs: dict[int, str] = {}

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    def _auth_headers(self) -> dict[str, str]:
        """Return Authorization header using the current request's token."""
        token = _current_token.get()
        if token:
            return {"Authorization": f"Bearer {token}"}
        return {}

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def ensure_auth(self, telegram_user_id: int) -> str | None:
        """Authenticate the Telegram user, returning a cached token or None."""
        if telegram_user_id in self._tokens:
            return self._tokens[telegram_user_id]
        session = await self._get_session()
        async with session.post(
            f"{self._base}/auth/telegram",
            json={"telegram_id": str(telegram_user_id)},
        ) as resp:
            if resp.status == 404:
                return None
            resp.raise_for_status()
            data = await resp.json()
        token = data["token"]
        self._tokens[telegram_user_id] = token
        return token

    async def get_user_language(self, telegram_user_id: int) -> str:
        """Return cached language or fetch from backend."""
        if telegram_user_id in self._langs:
            return self._langs[telegram_user_id]
        try:
            resp = await self._get("/settings/language")
            lang = resp.get("data", {}).get("language", "en-US")
        except Exception:
            lang = "en-US"
        self._langs[telegram_user_id] = lang
        return lang

    def set_cached_language(self, telegram_user_id: int, lang: str):
        """Update the cached language for a user."""
        self._langs[telegram_user_id] = lang

    async def link_telegram(self, code: str, telegram_user_id: int) -> dict:
        """Consume a link code and bind this Telegram account."""
        session = await self._get_session()
        async with session.post(
            f"{self._base}/auth/telegram-link",
            json={"code": code, "telegram_id": str(telegram_user_id)},
        ) as resp:
            if resp.status == 400:
                return {"status": "error", "message": "Invalid or expired link code"}
            resp.raise_for_status()
            data = await resp.json()
        self._tokens[telegram_user_id] = data["token"]
        return data

    async def disconnect(self, telegram_user_id: int) -> None:
        """Unlink Telegram account from the backend and clear cached token."""
        session = await self._get_session()
        try:
            await (
                await session.post(
                    f"{self._base}/auth/unlink-telegram",
                    json={"telegram_id": str(telegram_user_id)},
                )
            ).release()
        except Exception:
            pass  # best-effort
        self._tokens.pop(telegram_user_id, None)

    async def handle(self, request: dict) -> dict:
        action = request.get("action", "")
        data = request.get("data", {})
        try:
            return await self._dispatch(action, data)
        except aiohttp.ClientResponseError as exc:
            if exc.status == 401:
                self._clear_current_token()
                return {
                    "status": "error",
                    "message": "Session expired. Please reconnect from the CLI app.",
                }
            logger.exception("Backend HTTP error for action=%s", action)
            return {"status": "error", "message": str(exc)}
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

    def _clear_current_token(self):
        """Remove the cached token for the user whose request just failed."""
        token = _current_token.get()
        if token:
            # Find and remove the token from the cache
            for tg_id, cached in list(self._tokens.items()):
                if cached == token:
                    del self._tokens[tg_id]
                    break

    async def _get(self, path: str, params: dict | None = None) -> dict:
        session = await self._get_session()
        async with session.get(
            f"{self._base}{path}", params=params or {}, headers=self._auth_headers()
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def _post(self, path: str, body: dict | None = None) -> dict:
        session = await self._get_session()
        async with session.post(
            f"{self._base}{path}", json=body or {}, headers=self._auth_headers()
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def _put(self, path: str, body: dict | None = None) -> dict:
        session = await self._get_session()
        async with session.put(
            f"{self._base}{path}", json=body or {}, headers=self._auth_headers()
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def _delete(self, path: str, params: dict | None = None) -> dict:
        session = await self._get_session()
        async with session.delete(
            f"{self._base}{path}", params=params or {}, headers=self._auth_headers()
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def _dispatch(self, action: str, data: dict) -> dict:
        # Dashboard / general
        if action == "get_dashboard":
            return await self._get("/dashboard")
        if action == "get_portfolio":
            return await self._get("/portfolio")
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

        # Goals
        if action == "get_goals":
            return await self._get(
                "/goals", params={"filter": data.get("filter", "active")}
            )
        if action == "get_all_goals":
            return await self._get("/goals/all")
        if action == "get_goal_detail":
            return await self._get(f"/goals/{data['name']}")
        if action == "add_goal":
            return await self._post("/goals", body=data)
        if action == "complete_goal":
            return await self._post(f"/goals/{data['name']}/complete")
        if action == "hide_goal":
            return await self._post(f"/goals/{data['name']}/hide")
        if action == "reactivate_goal":
            return await self._post(f"/goals/{data['name']}/reactivate")
        if action == "save_to_goal":
            return await self._post("/goals/save", body=data)

        # Recurring transfers
        if action == "add_recurring_transfer":
            return await self._post("/recurring/transfer", body=data)
        if action == "add_recurring_goal_save":
            return await self._post("/recurring/goal-save", body=data)

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

        # Language settings
        if action == "get_language":
            return await self._get("/settings/language")
        if action == "set_language":
            return await self._post("/settings/language", body=data)

        return {"status": "error", "message": f"Unknown action: {action}"}


backend = Backend()
