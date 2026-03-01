# Budget Planner

A terminal-based personal budget planning app with a **FastAPI backend** and a **CLI frontend**.

---

## Getting Started

### Prerequisites

- Python 3.11+

### Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Running

Start the backend and frontend in two separate terminals.

**Terminal 1 — backend:**
```bash
cd app/backend && uvicorn app:app --host 0.0.0.0 --port 8080
```

**Terminal 2 — CLI frontend:**
```bash
cd app && python backend/main.py
```

**Terminal 3 — Telegram frontend:**
```bash
cd app && python -m telegram.bot
```

The backend URL can be configured via the `BACKEND_URL` environment variable (default: `http://localhost:8080`).

---

## Architecture

```
CLI Frontend (main.py + ui/) || Telegram Frontend(telegram/)
        │  HTTP (GET/POST/PUT/DELETE)
        ▼
FastAPI Backend (app.py)
        │
        ▼
Business Logic (api/, wallet/, models/, strategies/)
```

**Data flow:**
- **CLI:** `Display` collects user input → calls `HttpRequestHandler.handle({"action": "...", ...})` (sync HTTP)
- **Telegram:** aiogram handlers collect input via inline keyboards and FSM states → call `Backend.handle({"action": "...", ...})` (async HTTP via aiohttp)
- Both frontends send HTTP requests to the same FastAPI backend
- FastAPI routes the request → delegates to `RequestHandler` → business logic
- Response `{"status": "success|error", "message": "...", "data": {...}}` travels back to the frontend

---

## REST API

The backend exposes a full REST API. Interactive docs are available at `http://localhost:8080/docs` once the server is running.

| Method | Path | Description |
|--------|------|-------------|
| GET | `/dashboard` | Current wallet summary and transactions |
| GET | `/help` | List of available commands |
| GET | `/categories` | Transaction categories (`?transaction_type=income\|expense`) |
| GET | `/transactions/{index}` | Get a single transaction |
| POST | `/transactions` | Add a transaction |
| PUT | `/transactions/{index}` | Edit a transaction |
| DELETE | `/transactions/{index}` | Delete a transaction |
| GET | `/transfer` | Transfer context (available wallets) |
| POST | `/transfer` | Execute a transfer between wallets |
| GET | `/sorting` | Available transaction sorting options |
| POST | `/sorting` | Set transaction sorting |
| GET | `/sorting/wallets` | Available wallet sorting options |
| POST | `/sorting/wallets` | Set wallet sorting |
| GET | `/filters` | Active filters |
| POST | `/filters` | Add a filter |
| DELETE | `/filters` | Clear all filters |
| DELETE | `/filters/{index}` | Remove a single filter |
| GET | `/percentages` | Category breakdown percentages |
| GET | `/wallets` | List all wallets |
| POST | `/wallets` | Create a wallet |
| GET | `/wallets/{name}` | Wallet detail |
| PUT | `/wallets/{name}` | Edit a wallet |
| DELETE | `/wallets/{name}` | Delete a wallet |
| POST | `/wallets/switch` | Switch active wallet |
| GET | `/recurring` | List recurring transactions |
| POST | `/recurring` | Create a recurring transaction |
| GET | `/recurring/{index}` | Recurring transaction detail |
| PUT | `/recurring/{index}` | Edit a recurring transaction |
| DELETE | `/recurring/{index}` | Delete a recurring transaction |
| POST | `/recurring/process` | Materialise overdue recurring transactions |

---

## Telegram Frontend

The Telegram bot is an alternative frontend built with **aiogram 3.x**. It connects to the same FastAPI backend as the CLI.

### Setup

Create a `.env` file in the project root:
```
TELEGRAM_BOT_TOKEN=<your-bot-token-from-@BotFather>
BACKEND_URL=http://localhost:8000
```

### Running

```bash
python -m app.telegram.bot
```

### Key Features

- Inline keyboard-driven UI (no typed commands required, though slash commands are supported)
- Multi-step conversation flows powered by aiogram FSM (`MemoryStorage`)
- Full feature parity with the CLI: transactions, transfers, wallets (regular + deposit), recurring transactions, sorting, filters, percentages
- MarkdownV2 formatted output with safe escaping of user data
- Text shortcuts: `show N`, `wallet NAME`, `switch NAME`

### Limitations

- FSM state is in-memory and not persisted across bot restarts
- No multi-user isolation — all Telegram users share the same backend data

---

## Project Structure

```
app/
├── app.py                   # FastAPI backend entry point
├── main.py                  # CLI frontend entry point
├── logger_setup.py          # Logging configuration
├── api/
│   ├── request_handler.py   # Business-logic dispatcher (~30 actions)
│   └── http_handler.py      # HTTP client adapter (mirrors RequestHandler interface)
├── wallet/
│   ├── wallet.py            # Wallet and DepositWallet classes
│   └── wallet_manager.py    # Wallet collection + inter-wallet transfers
├── models/
│   ├── transaction.py       # Transaction and Transfer dataclasses
│   ├── recurrence.py        # RecurrenceRule and RecurringTransaction
│   └── recurrence_scheduler.py
├── strategies/
│   ├── filtering.py         # Pluggable filter strategies
│   └── sorting.py           # Pluggable sort strategies
├── ui/
│   ├── display.py           # Main loop, command routing, rendering
│   └── input_handler.py     # User input collection
└── telegram/
    ├── bot.py               # Telegram bot entry point (aiogram 3.x)
    ├── config.py            # BOT_TOKEN and BACKEND_URL from .env
    ├── backend.py           # Async HTTP client (same interface as http_handler)
    ├── states.py            # FSM state groups for conversation flows
    ├── keyboards.py         # Inline keyboard builders
    ├── utils.py             # MarkdownV2 response formatters
    └── handlers/
        ├── dashboard.py     # /start, /dashboard
        ├── transactions.py  # Add/edit/delete/show transactions
        ├── transfers.py     # Inter-wallet transfers
        ├── wallets.py       # Wallet CRUD + switch
        ├── recurring.py     # Recurring transaction management
        ├── sorting.py       # Transaction and wallet sorting
        ├── filters.py       # Filter management
        ├── percentages.py   # Category breakdown
        ├── help.py          # Static help text
        └── common.py        # Cancel + text shortcuts (catch-all)
```

---

## Development

Activate the virtual environment:
```bash
source .venv/bin/activate
```

Run linting and tests (mirrors CI):
```bash
run_checks.sh
```

Auto-fix formatting:
```bash
black .
```

### Adding a New Feature

1. Add a handler method in `app/api/request_handler.py` and register it in `_routes`.
2. Add the corresponding endpoint in `app/app.py`.
3. Add the routing branch in `app/api/http_handler.py` (`_dispatch`) for the CLI.
4. Add the routing branch in `app/telegram/backend.py` (`_dispatch`) for the Telegram bot.
5. Wire up CLI UI in `app/ui/display.py`.
6. Wire up Telegram UI: add handler in `app/telegram/handlers/`, states in `states.py`, keyboards in `keyboards.py`, formatters in `utils.py`, and register the router in `bot.py`.
