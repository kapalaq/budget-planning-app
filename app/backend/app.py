"""FastAPI backend for the budget planner."""

import asyncio
import logging
import os
import sys

from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from contextlib import asynccontextmanager
from typing import Any, Dict

import logger_setup
from api.request_handler import RequestHandler
from data.mongo import get_mongo_db
from data.postgres import get_postgres_conn
from db.session_manager import SessionManager
from db.storage import MongoStorage
from db.user_preferences import UserPreferences
from db.user_store import UserStore
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from wallet.wallet import Wallet
from wallet.wallet_manager import WalletManager

# Some initial calls
load_dotenv()

logger = logging.getLogger(__name__)

# Per-user state
_user_managers: dict[int, WalletManager] = {}
_user_handlers: dict[int, RequestHandler] = {}
_dirty_users: set[int] = set()
_storage: MongoStorage | None = None
_user_store: UserStore | None = None
_user_prefs: UserPreferences | None = None
_session_manager: SessionManager | None = None

AUTOSAVE_INTERVAL = 60  # seconds (5 minutes)


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


def _save_dirty_users():
    """Save all users marked as dirty and clear the dirty set."""
    if not _dirty_users:
        return
    for user_id in list(_dirty_users):
        if user_id in _user_managers:
            _storage.save(
                user_id, {"wallet_manager": _user_managers[user_id].to_json()}
            )
    logger.info("Auto-saved %d user(s).", len(_dirty_users))
    _dirty_users.clear()


async def _autosave_loop():
    """Background task: save dirty users every AUTOSAVE_INTERVAL seconds."""
    while True:
        await asyncio.sleep(AUTOSAVE_INTERVAL)
        try:
            _save_dirty_users()
        except Exception:
            logger.exception("Auto-save failed")


# Entry point
@asynccontextmanager
async def lifespan(app: FastAPI):
    global _storage, _user_store, _user_prefs, _session_manager

    # PostgreSQL for user authentication
    postgres_dsn = os.getenv(
        "POSTGRES_DSN",
        "postgresql://postgres:postgres@localhost:5432/budget_planner",
    )
    pg_conn = get_postgres_conn(postgres_dsn)
    _user_store = UserStore(pg_conn)

    # MongoDB for session management
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    mongo_db_name = os.getenv("MONGO_DB", "budget_planner")
    mongo_db = get_mongo_db(mongo_uri, mongo_db_name)
    _session_manager = SessionManager(mongo_db)
    _storage = MongoStorage(mongo_db)
    _user_prefs = UserPreferences(mongo_db)

    autosave_task = asyncio.create_task(_autosave_loop())

    yield

    autosave_task.cancel()
    logger.info("Shutting down... Saving all user data.")
    _dirty_users.update(_user_managers.keys())
    _save_dirty_users()


app = FastAPI(title="Budget Planner API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


# Actions that only read data and don't need saving
_READ_ONLY_ACTIONS = frozenset(
    {
        "get_dashboard",
        "get_help",
        "get_categories",
        "suggest_amount",
        "get_transaction",
        "get_transfer_context",
        "get_sorting_options",
        "get_wallet_sorting_options",
        "get_active_filters",
        "get_percentages",
        "get_wallets",
        "get_wallet_detail",
        "get_recurring_list",
        "get_recurring_detail",
        "get_goals",
        "get_all_goals",
        "get_goal_detail",
        "get_bills",
        "get_all_bills",
        "get_bill_detail",
    }
)


def _handle(user_id: int, action: str, data: dict | None = None) -> dict:
    """Route an action to the correct per-user handler."""
    _, handler = _get_manager(user_id)
    lang = _user_prefs.get_language(user_id)
    tz_offset = _user_prefs.get_timezone(user_id)
    result = handler.handle(
        {"action": action, "data": data or {}}, lang=lang, tz_offset=tz_offset
    )
    if action not in _READ_ONLY_ACTIONS:
        _dirty_users.add(user_id)
    return result


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


@app.post("/auth/link-code")
def auth_link_code(user_id: int = Depends(get_current_user)):
    """Generate a deep-link code for binding a Telegram account."""
    code = _session_manager.create_link_code(user_id)
    bot_username = os.getenv("TELEGRAM_BOT_USERNAME", "")
    deep_link = f"https://t.me/{bot_username}?start={code}" if bot_username else ""
    return {"status": "success", "code": code, "deep_link": deep_link}


@app.post("/auth/telegram-link")
def auth_telegram_link(body: Dict[str, Any]):
    """Consume a link code and bind a Telegram account to the user."""
    code = body.get("code", "")
    telegram_id = str(body.get("telegram_id", ""))
    if not code or not telegram_id:
        raise HTTPException(status_code=400, detail="code and telegram_id are required")
    user_id = _session_manager.consume_link_code(code)
    if user_id is None:
        raise HTTPException(status_code=400, detail="Invalid or expired link code")
    _user_store.update_telegram_id(user_id, telegram_id)
    token = _session_manager.create_session(user_id)
    return {"status": "success", "token": token, "user_id": user_id}


@app.post("/auth/unlink-telegram")
def auth_unlink_telegram(body: Dict[str, Any]):
    """Unlink a Telegram account from its user."""
    telegram_id = str(body.get("telegram_id", ""))
    if not telegram_id:
        raise HTTPException(status_code=400, detail="telegram_id is required")
    _user_store.clear_telegram_id(telegram_id)
    return {"status": "success", "message": "Telegram account unlinked"}


# Health check
@app.get("/health")
def health_check():
    return {"status": "success"}


#  Language settings
@app.get("/settings/language")
def get_language(user_id: int = Depends(get_current_user)):
    lang = _user_prefs.get_language(user_id)
    return {"status": "success", "data": {"language": lang}}


@app.post("/settings/language")
def set_language(body: Dict[str, Any], user_id: int = Depends(get_current_user)):
    lang = body.get("language", "en-US")
    from languages import AVAILABLE_LANGUAGES, t

    if lang not in AVAILABLE_LANGUAGES:
        raise HTTPException(status_code=400, detail=f"Unsupported language: {lang}")
    _user_prefs.set_language(user_id, lang)
    return {
        "status": "success",
        "message": f"Language changed to {AVAILABLE_LANGUAGES[lang]}",
        "data": {"language": lang},
    }


#  Timezone settings
VALID_OFFSETS = set(range(-12, 15))


@app.get("/settings/timezone")
def get_timezone(user_id: int = Depends(get_current_user)):
    tz = _user_prefs.get_timezone(user_id)
    return {"status": "success", "data": {"timezone": tz}}


@app.post("/settings/timezone")
def set_timezone(body: Dict[str, Any], user_id: int = Depends(get_current_user)):
    tz = body.get("timezone", 0)
    if not isinstance(tz, int) or tz not in VALID_OFFSETS:
        raise HTTPException(status_code=400, detail=f"Invalid timezone offset: {tz}")
    _user_prefs.set_timezone(user_id, tz)
    sign = "+" if tz >= 0 else ""
    return {
        "status": "success",
        "message": f"Timezone changed to GMT{sign}{tz}",
        "data": {"timezone": tz},
    }


#  Hidden chart categories
@app.get("/settings/hidden-chart-categories")
def get_hidden_chart_categories(user_id: int = Depends(get_current_user)):
    data = _user_prefs.get_hidden_chart_categories(user_id)
    return {"status": "success", "data": data}


@app.post("/settings/hidden-chart-categories")
def set_hidden_chart_categories(
    body: Dict[str, Any], user_id: int = Depends(get_current_user)
):
    _user_prefs.set_hidden_chart_categories(user_id, body)
    return {"status": "success", "message": "Chart category visibility updated"}


#  Category colors
@app.get("/settings/category-colors")
def get_category_colors(user_id: int = Depends(get_current_user)):
    data = _user_prefs.get_category_colors(user_id)
    return {"status": "success", "data": data}


@app.post("/settings/category-colors")
def set_category_colors(body: Dict[str, Any], user_id: int = Depends(get_current_user)):
    _user_prefs.set_category_colors(user_id, body)
    return {"status": "success", "message": "Category colors updated"}


#  Dashboard / General
@app.get("/dashboard")
def get_dashboard(user_id: int = Depends(get_current_user)):
    return _handle(user_id, "get_dashboard")


@app.get("/portfolio")
async def get_portfolio(user_id: int = Depends(get_current_user)):
    """Cross-currency portfolio totals using live exchange rates."""
    from services.currency import currency_service

    wm, _ = _get_manager(user_id)
    base_currency = wm.current_wallet.currency if wm.current_wallet else "USD"

    wallets_data = []
    total_converted = 0.0
    rates_available = True

    for w in wm.get_visible_wallets():
        converted = await currency_service.convert(w.balance, w.currency, base_currency)
        if converted is None:
            rates_available = False
            converted = w.balance if w.currency == base_currency else 0.0
        total_converted += converted
        wallets_data.append(
            {
                "name": w.name,
                "currency": w.currency,
                "balance": w.balance,
                "converted": round(converted, 2),
            }
        )

    return {
        "status": "success",
        "data": {
            "base_currency": base_currency,
            "total_balance": round(total_converted, 2),
            "wallets": wallets_data,
            "rates_available": rates_available,
        },
    }


@app.get("/currency/convert")
async def convert_currency(amount: float, from_currency: str, to_currency: str):
    """Convert amount between currencies using live exchange rates."""
    from services.currency import currency_service

    converted = await currency_service.convert(amount, from_currency, to_currency)
    return {
        "status": "success",
        "data": {"converted": converted},
    }


@app.get("/help")
def get_help(user_id: int = Depends(get_current_user)):
    return _handle(user_id, "get_help")


#  Categories
@app.get("/categories")
def get_categories(
    transaction_type: str = "expense", user_id: int = Depends(get_current_user)
):
    return _handle(user_id, "get_categories", {"transaction_type": transaction_type})


#  Suggest amount
@app.get("/suggest-amount")
def suggest_amount(
    category: str,
    transaction_type: str = "expense",
    user_id: int = Depends(get_current_user),
):
    return _handle(
        user_id,
        "suggest_amount",
        {"category": category, "transaction_type": transaction_type},
    )


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


#  Goals
@app.get("/goals")
def get_goals(filter: str = "active", user_id: int = Depends(get_current_user)):
    return _handle(user_id, "get_goals", {"filter": filter})


@app.post("/goals")
def add_goal(body: Dict[str, Any], user_id: int = Depends(get_current_user)):
    return _handle(user_id, "add_goal", body)


@app.get("/goals/all")
def get_all_goals(user_id: int = Depends(get_current_user)):
    return _handle(user_id, "get_all_goals")


@app.get("/goals/{name}")
def get_goal_detail(name: str, user_id: int = Depends(get_current_user)):
    return _handle(user_id, "get_goal_detail", {"name": name})


@app.post("/goals/{name}/complete")
def complete_goal(name: str, user_id: int = Depends(get_current_user)):
    return _handle(user_id, "complete_goal", {"name": name})


@app.post("/goals/{name}/hide")
def hide_goal(name: str, user_id: int = Depends(get_current_user)):
    return _handle(user_id, "hide_goal", {"name": name})


@app.post("/goals/{name}/reactivate")
def reactivate_goal(name: str, user_id: int = Depends(get_current_user)):
    return _handle(user_id, "reactivate_goal", {"name": name})


@app.post("/goals/save")
def save_to_goal(body: Dict[str, Any], user_id: int = Depends(get_current_user)):
    return _handle(user_id, "save_to_goal", body)


@app.delete("/goals/{name}")
def delete_goal(name: str, user_id: int = Depends(get_current_user)):
    return _handle(user_id, "delete_goal", {"name": name})


#  Bills
@app.get("/bills")
def get_bills(filter: str = "active", user_id: int = Depends(get_current_user)):
    return _handle(user_id, "get_bills", {"filter": filter})


@app.post("/bills")
def add_bill(body: Dict[str, Any], user_id: int = Depends(get_current_user)):
    return _handle(user_id, "add_bill", body)


@app.get("/bills/all")
def get_all_bills(user_id: int = Depends(get_current_user)):
    return _handle(user_id, "get_all_bills")


@app.get("/bills/{name}")
def get_bill_detail(name: str, user_id: int = Depends(get_current_user)):
    return _handle(user_id, "get_bill_detail", {"name": name})


@app.post("/bills/{name}/complete")
def complete_bill(name: str, user_id: int = Depends(get_current_user)):
    return _handle(user_id, "complete_bill", {"name": name})


@app.post("/bills/{name}/hide")
def hide_bill(name: str, user_id: int = Depends(get_current_user)):
    return _handle(user_id, "hide_bill", {"name": name})


@app.post("/bills/{name}/reactivate")
def reactivate_bill(name: str, user_id: int = Depends(get_current_user)):
    return _handle(user_id, "reactivate_bill", {"name": name})


@app.post("/bills/save")
def save_to_bill(body: Dict[str, Any], user_id: int = Depends(get_current_user)):
    return _handle(user_id, "save_to_bill", body)


@app.delete("/bills/{name}")
def delete_bill(name: str, user_id: int = Depends(get_current_user)):
    return _handle(user_id, "delete_bill", {"name": name})


#  Recurring transfers
@app.post("/recurring/transfer")
def add_recurring_transfer(
    body: Dict[str, Any], user_id: int = Depends(get_current_user)
):
    return _handle(user_id, "add_recurring_transfer", body)


@app.post("/recurring/goal-save")
def add_recurring_goal_save(
    body: Dict[str, Any], user_id: int = Depends(get_current_user)
):
    return _handle(user_id, "add_recurring_goal_save", body)


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
