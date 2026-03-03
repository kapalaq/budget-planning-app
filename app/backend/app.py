"""FastAPI backend for the budget planner."""

import logging
import os
import sys

from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from typing import Any, Dict
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, Header, HTTPException

import logger_setup
from api.request_handler import RequestHandler
from auth.session_manager import SessionManager
from data.storage import JsonStorage
from data.user_store import UserStore
from wallet.wallet import Wallet
from wallet.wallet_manager import WalletManager

# Some initial calls
load_dotenv()

logger = logging.getLogger(__name__)

# Per-user state
_user_managers: dict[int, WalletManager] = {}
_user_handlers: dict[int, RequestHandler] = {}
_storage: JsonStorage | None = None
_user_store: UserStore | None = None
_session_manager: SessionManager | None = None


def _get_manager(user_id: int) -> tuple[WalletManager, RequestHandler]:
    """Load or retrieve the cached WalletManager and RequestHandler for a user."""
    if user_id not in _user_managers:
        data = _storage.load(user_id)
        wm = WalletManager().from_json(data.get("wallet_manager"))
        if len(wm.get_wallets()) == 0:
            wm.add_wallet(Wallet(name="Main Wallet", currency="KZT"))
        _user_managers[user_id] = wm
        _user_handlers[user_id] = RequestHandler(wm)
    return _user_managers[user_id], _user_handlers[user_id]


# Entry point
@asynccontextmanager
async def lifespan(app: FastAPI):
    global _storage, _user_store, _session_manager

    data_dir = os.path.join(os.getcwd(), os.getenv("DATA_DIR", "data"))
    _storage = JsonStorage(os.path.join(data_dir, "jsons"))
    _user_store = UserStore(os.path.join(data_dir, "user_auth", "users.csv"))
    _session_manager = SessionManager()

    yield

    logger.info("Shutting down... Saving all user data.")
    for user_id, wm in _user_managers.items():
        _storage.save(user_id, {"wallet_manager": wm.to_json()})


app = FastAPI(title="Budget Planner API", lifespan=lifespan)


# Auth dependency
def get_current_user(authorization: str = Header()) -> int:
    """Extract user_id from the Authorization: Bearer <token> header."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    token = authorization[len("Bearer ") :]
    user_id = _session_manager.get_user_id(token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user_id


def _handle(user_id: int, action: str, data: dict | None = None) -> dict:
    """Route an action to the correct per-user handler."""
    _, handler = _get_manager(user_id)
    return handler.handle({"action": action, "data": data or {}})


# Auth endpoints
@app.post("/auth/login")
def auth_login(body: Dict[str, Any]):
    login = body.get("login", "")
    password = body.get("password", "")
    telegram_id = body.get("telegram_id", "")
    user_id = _user_store.authenticate(login, password)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid login or password")
    if telegram_id:
        _user_store.update_telegram_id(user_id, telegram_id)
    token = _session_manager.create_session(user_id)
    return {"status": "success", "token": token, "user_id": user_id}


@app.post("/auth/register")
def auth_register(body: Dict[str, Any]):
    login = body.get("login", "")
    password = body.get("password", "")
    telegram_id = body.get("telegram_id", "")
    user_id = _user_store.register(login, password, telegram_id)
    if user_id is None:
        raise HTTPException(status_code=409, detail="Login already taken")
    token = _session_manager.create_session(user_id)
    return {"status": "success", "token": token, "user_id": user_id}


@app.post("/auth/telegram")
def auth_telegram(body: Dict[str, Any]):
    telegram_id = str(body.get("telegram_id", ""))
    if not telegram_id:
        raise HTTPException(status_code=400, detail="telegram_id is required")
    user_id = _user_store.authenticate_by_telegram_id(telegram_id)
    if user_id is None:
        raise HTTPException(status_code=404, detail="Telegram account not linked")
    token = _session_manager.create_session(user_id)
    return {"status": "success", "token": token, "user_id": user_id}


# Health check
@app.get("/health")
def health_check():
    return {"status": "success"}


#  Dashboard / General
@app.get("/dashboard")
def get_dashboard(user_id: int = Depends(get_current_user)):
    return _handle(user_id, "get_dashboard")


@app.get("/help")
def get_help(user_id: int = Depends(get_current_user)):
    return _handle(user_id, "get_help")


#  Categories
@app.get("/categories")
def get_categories(
    transaction_type: str = "expense", user_id: int = Depends(get_current_user)
):
    return _handle(user_id, "get_categories", {"transaction_type": transaction_type})


#  Transactions
@app.get("/transactions/{index}")
def get_transaction(index: int, user_id: int = Depends(get_current_user)):
    return _handle(user_id, "get_transaction", {"index": index})


@app.post("/transactions")
def add_transaction(body: Dict[str, Any], user_id: int = Depends(get_current_user)):
    return _handle(user_id, "add_transaction", body)


@app.put("/transactions/{index}")
def edit_transaction(
    index: int, body: Dict[str, Any], user_id: int = Depends(get_current_user)
):
    return _handle(user_id, "edit_transaction", {"index": index, **body})


@app.delete("/transactions/{index}")
def delete_transaction(index: int, user_id: int = Depends(get_current_user)):
    return _handle(user_id, "delete_transaction", {"index": index})


#  Transfer
@app.get("/transfer")
def get_transfer_context(user_id: int = Depends(get_current_user)):
    return _handle(user_id, "get_transfer_context")


@app.post("/transfer")
def transfer(body: Dict[str, Any], user_id: int = Depends(get_current_user)):
    return _handle(user_id, "transfer", body)


#  Sorting
@app.get("/sorting")
def get_sorting_options(user_id: int = Depends(get_current_user)):
    return _handle(user_id, "get_sorting_options")


@app.post("/sorting")
def set_sorting(body: Dict[str, Any], user_id: int = Depends(get_current_user)):
    return _handle(user_id, "set_sorting", body)


@app.get("/sorting/wallets")
def get_wallet_sorting_options(user_id: int = Depends(get_current_user)):
    return _handle(user_id, "get_wallet_sorting_options")


@app.post("/sorting/wallets")
def set_wallet_sorting(body: Dict[str, Any], user_id: int = Depends(get_current_user)):
    return _handle(user_id, "set_wallet_sorting", body)


#  Filters
@app.get("/filters")
def get_active_filters(user_id: int = Depends(get_current_user)):
    return _handle(user_id, "get_active_filters")


@app.post("/filters")
def add_filter(body: Dict[str, Any], user_id: int = Depends(get_current_user)):
    return _handle(user_id, "add_filter", body)


# Specific path before parameterised path so FastAPI matches correctly
@app.delete("/filters")
def clear_filters(user_id: int = Depends(get_current_user)):
    return _handle(user_id, "clear_filters")


@app.delete("/filters/{index}")
def remove_filter(index: int, user_id: int = Depends(get_current_user)):
    return _handle(user_id, "remove_filter", {"filter_index": index})


#  Percentages
@app.get("/percentages")
def get_percentages(user_id: int = Depends(get_current_user)):
    return _handle(user_id, "get_percentages")


#  Wallets
@app.get("/wallets")
def get_wallets(user_id: int = Depends(get_current_user)):
    return _handle(user_id, "get_wallets")


@app.post("/wallets")
def add_wallet(body: Dict[str, Any], user_id: int = Depends(get_current_user)):
    return _handle(user_id, "add_wallet", body)


# Specific path before parameterised path so FastAPI matches correctly
@app.post("/wallets/switch")
def switch_wallet(body: Dict[str, Any], user_id: int = Depends(get_current_user)):
    return _handle(user_id, "switch_wallet", body)


@app.get("/wallets/{name}")
def get_wallet_detail(name: str, user_id: int = Depends(get_current_user)):
    return _handle(user_id, "get_wallet_detail", {"name": name})


@app.put("/wallets/{name}")
def edit_wallet(
    name: str, body: Dict[str, Any], user_id: int = Depends(get_current_user)
):
    return _handle(user_id, "edit_wallet", {"name": name, **body})


@app.delete("/wallets/{name}")
def delete_wallet(name: str, user_id: int = Depends(get_current_user)):
    return _handle(user_id, "delete_wallet", {"name": name})


#  Recurring
@app.post("/recurring/process")
def process_recurring(user_id: int = Depends(get_current_user)):
    return _handle(user_id, "process_recurring")


@app.get("/recurring")
def get_recurring_list(user_id: int = Depends(get_current_user)):
    return _handle(user_id, "get_recurring_list")


@app.post("/recurring")
def add_recurring(body: Dict[str, Any], user_id: int = Depends(get_current_user)):
    return _handle(user_id, "add_recurring", body)


@app.get("/recurring/{index}")
def get_recurring_detail(index: int, user_id: int = Depends(get_current_user)):
    return _handle(user_id, "get_recurring_detail", {"index": index})


@app.put("/recurring/{index}")
def edit_recurring(
    index: int, body: Dict[str, Any], user_id: int = Depends(get_current_user)
):
    return _handle(user_id, "edit_recurring", {"index": index, **body})


@app.delete("/recurring/{index}")
def delete_recurring(
    index: int,
    delete_option: int = 1,
    user_id: int = Depends(get_current_user),
):
    return _handle(
        user_id,
        "delete_recurring",
        {"index": index, "delete_option": delete_option},
    )
