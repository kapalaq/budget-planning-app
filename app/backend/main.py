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


def main():
    handler = HttpRequestHandler()
    display = Display(handler)
    display.run()


if __name__ == "__main__":
    main()
