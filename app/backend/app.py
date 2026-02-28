"""FastAPI backend for the budget planner."""

import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from typing import Any, Dict

import uvicorn
from fastapi import FastAPI

import logger_setup
from api.request_handler import RequestHandler
from wallet.wallet import Wallet
from wallet.wallet_manager import WalletManager

logger = logging.getLogger(__name__)

app = FastAPI(title="Budget Planner API")

# Initialise backend state once at startup
_wallet_manager = WalletManager()
_wallet_manager.add_wallet(Wallet(name="Main Wallet", currency="KZT"))
_handler = RequestHandler(_wallet_manager)


#  Dashboard / General
@app.get("/dashboard")
def get_dashboard():
    return _handler.handle({"action": "get_dashboard", "data": {}})


@app.get("/help")
def get_help():
    return _handler.handle({"action": "get_help", "data": {}})


#  Categories
@app.get("/categories")
def get_categories(transaction_type: str = "expense"):
    return _handler.handle(
        {"action": "get_categories", "data": {"transaction_type": transaction_type}}
    )


#  Transactions
@app.get("/transactions/{index}")
def get_transaction(index: int):
    return _handler.handle({"action": "get_transaction", "data": {"index": index}})


@app.post("/transactions")
def add_transaction(body: Dict[str, Any]):
    return _handler.handle({"action": "add_transaction", "data": body})


@app.put("/transactions/{index}")
def edit_transaction(index: int, body: Dict[str, Any]):
    return _handler.handle(
        {"action": "edit_transaction", "data": {"index": index, **body}}
    )


@app.delete("/transactions/{index}")
def delete_transaction(index: int):
    return _handler.handle({"action": "delete_transaction", "data": {"index": index}})


#  Transfer
@app.get("/transfer")
def get_transfer_context():
    return _handler.handle({"action": "get_transfer_context", "data": {}})


@app.post("/transfer")
def transfer(body: Dict[str, Any]):
    return _handler.handle({"action": "transfer", "data": body})


#  Sorting
@app.get("/sorting")
def get_sorting_options():
    return _handler.handle({"action": "get_sorting_options", "data": {}})


@app.post("/sorting")
def set_sorting(body: Dict[str, Any]):
    return _handler.handle({"action": "set_sorting", "data": body})


@app.get("/sorting/wallets")
def get_wallet_sorting_options():
    return _handler.handle({"action": "get_wallet_sorting_options", "data": {}})


@app.post("/sorting/wallets")
def set_wallet_sorting(body: Dict[str, Any]):
    return _handler.handle({"action": "set_wallet_sorting", "data": body})


#  Filters
@app.get("/filters")
def get_active_filters():
    return _handler.handle({"action": "get_active_filters", "data": {}})


@app.post("/filters")
def add_filter(body: Dict[str, Any]):
    return _handler.handle({"action": "add_filter", "data": body})


# Specific path before parameterised path so FastAPI matches correctly
@app.delete("/filters")
def clear_filters():
    return _handler.handle({"action": "clear_filters", "data": {}})


@app.delete("/filters/{index}")
def remove_filter(index: int):
    return _handler.handle({"action": "remove_filter", "data": {"filter_index": index}})


#  Percentages
@app.get("/percentages")
def get_percentages():
    return _handler.handle({"action": "get_percentages", "data": {}})


#  Wallets
@app.get("/wallets")
def get_wallets():
    return _handler.handle({"action": "get_wallets", "data": {}})


@app.post("/wallets")
def add_wallet(body: Dict[str, Any]):
    return _handler.handle({"action": "add_wallet", "data": body})


# Specific path before parameterised path so FastAPI matches correctly
@app.post("/wallets/switch")
def switch_wallet(body: Dict[str, Any]):
    return _handler.handle({"action": "switch_wallet", "data": body})


@app.get("/wallets/{name}")
def get_wallet_detail(name: str):
    return _handler.handle({"action": "get_wallet_detail", "data": {"name": name}})


@app.put("/wallets/{name}")
def edit_wallet(name: str, body: Dict[str, Any]):
    return _handler.handle({"action": "edit_wallet", "data": {"name": name, **body}})


@app.delete("/wallets/{name}")
def delete_wallet(name: str):
    return _handler.handle({"action": "delete_wallet", "data": {"name": name}})


#  Recurring
@app.post("/recurring/process")
def process_recurring():
    return _handler.handle({"action": "process_recurring", "data": {}})


@app.get("/recurring")
def get_recurring_list():
    return _handler.handle({"action": "get_recurring_list", "data": {}})


@app.post("/recurring")
def add_recurring(body: Dict[str, Any]):
    return _handler.handle({"action": "add_recurring", "data": body})


@app.get("/recurring/{index}")
def get_recurring_detail(index: int):
    return _handler.handle({"action": "get_recurring_detail", "data": {"index": index}})


@app.put("/recurring/{index}")
def edit_recurring(index: int, body: Dict[str, Any]):
    return _handler.handle(
        {"action": "edit_recurring", "data": {"index": index, **body}}
    )


@app.delete("/recurring/{index}")
def delete_recurring(index: int, delete_option: int = 1):
    return _handler.handle(
        {
            "action": "delete_recurring",
            "data": {"index": index, "delete_option": delete_option},
        }
    )
