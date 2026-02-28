"""
Budget Planner - A modular budget planning system.

This is the main entry point for the application.
Run with: python main.py
"""

import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import BudgetPlannerApp


def main():
    """Main entry point."""
    app = BudgetPlannerApp()
    app.run()


if __name__ == "__main__":
    main()
