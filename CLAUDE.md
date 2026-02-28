# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the Application

```bash
python main.py
```

No external dependencies — pure Python (3.11+). No installation step required.

## Code Quality Commands

Install linting tools first:
```bash
pip install black flake8 isort bandit
```

Then run checks locally (mirroring CI):
```bash
black --check .
isort --check-only .
flake8 --ignore=E203,E501,W291,W293,W391 .
bandit -r .
```

To auto-fix formatting:
```bash
black .
isort .
```

## Architecture

The app uses a **3-tier architecture** with dict-based messaging between layers:

```
UI Layer (ui/) → API Layer (api/) → Business Logic (wallet/, models/, strategies/)
```

**Data flow:** `Display` collects user input → sends `{"action": "...", ...}` dicts to `RequestHandler` → routes to business logic → returns `{"status": "success|error", "message": "...", "data": {...}}` → `Display` renders.

### Key Modules

- **`api/request_handler.py`** — Central dispatcher (~30 actions). All UI↔backend communication goes through here. Add new features by registering new action handlers here.
- **`wallet/wallet_manager.py`** — Manages the collection of wallets and inter-wallet transfers. Owns the `RecurrenceScheduler`.
- **`wallet/wallet.py`** — `Wallet` and `DepositWallet` classes. Each wallet owns its transaction list and applies filtering/sorting strategies.
- **`models/transaction.py`** — `Transaction` and `Transfer` dataclasses. `Transfer` maintains a bidirectional link (`connected_transaction`) to its counterpart in another wallet.
- **`models/recurrence.py`** — `RecurrenceRule` and `RecurringTransaction`. Rules support Daily/Weekly/Monthly/Yearly frequencies with nth-weekday-of-month patterns.
- **`models/recurrence_scheduler.py`** — Materializes overdue recurring transactions on each app cycle.
- **`strategies/filtering.py`** / **`strategies/sorting.py`** — Strategy pattern for pluggable filtering and sorting. `CompositeFilter` ANDs multiple filters together.
- **`ui/display.py`** — Main loop, command routing, all rendering logic.
- **`ui/input_handler.py`** — All user input collection (amounts, dates, categories, menus).

### Important Conventions

- **"Transfer" is a reserved category** — never used for regular transactions; enforced in `CategoryManager`.
- **Request/response dicts** are the contract between UI and API layers. Do not call business logic directly from `display.py`.
- **`RecurrenceScheduler.process()`** is called at the start of each display cycle to materialize pending recurring transactions before showing the dashboard.
- Logging is configured in `logger_setup.py` and writes to both stderr and `app.log`.