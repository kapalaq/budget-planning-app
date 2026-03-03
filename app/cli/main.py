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


def main():
    handler = HttpRequestHandler()

    if not _auth_prompt(handler):
        print("Goodbye!")
        return

    display = Display(handler)
    display.run()


if __name__ == "__main__":
    main()
