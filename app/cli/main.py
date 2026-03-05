"""
Budget Planner - CLI frontend.

Connects to the FastAPI backend and runs the terminal UI.

Start the backend first:
    uvicorn app:app --host 0.0.0.0 --port 8000

Then run the CLI:
    python main.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.http_handler import HttpRequestHandler
from ui.display import Display


def _auth_prompt(handler: HttpRequestHandler) -> bool:
    """Prompt user to login or register. Returns True on success."""
    while True:
        print("\n=== Budget Planner ===")
        print("1. Login")
        print("2. Register")
        print("3. Exit")
        choice = input("Choose an option: ").strip()

        if choice == "3":
            return False

        if choice not in ("1", "2"):
            print("Invalid choice. Please try again.")
            continue

        login = input("Login: ").strip()
        password = input("Password: ").strip()

        if not login or not password:
            print("Login and password cannot be empty.")
            continue

        if choice == "1":
            result = handler.login(login, password)
        else:
            result = handler.register(login, password)

        if result.get("status") == "error":
            print(f"Error: {result['message']}")
            continue

        print(f"Welcome! (user_id: {result['user_id']})")
        return True


def _offer_telegram_link(handler: HttpRequestHandler):
    """Offer the user to generate a Telegram deep link."""
    choice = input("\nLink Telegram account? (y/N): ").strip().lower()
    if choice != "y":
        return
    result = handler.generate_link_code()
    if result.get("status") == "error":
        print(f"Error: {result['message']}")
        return
    deep_link = result.get("deep_link", "")
    code = result.get("code", "")
    if deep_link:
        print(f"\nOpen this link in Telegram to connect your account:\n  https://t.me/{deep_link}")
    else:
        print(f"\nSend this to the bot via /start {code}")
        print("(Set BOT_USERNAME in .env to get a clickable link)")
    print("The link expires in 5 minutes.")


def main():
    handler = HttpRequestHandler()

    if not _auth_prompt(handler):
        print("Goodbye!")
        return

    _offer_telegram_link(handler)

    display = Display(handler)
    display.run()


if __name__ == "__main__":
    main()
