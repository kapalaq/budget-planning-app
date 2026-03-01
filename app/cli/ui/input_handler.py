"""Input handling utilities for the budget planner (frontend side)."""

from datetime import datetime
from typing import Dict, List, Optional, Tuple


class InputHandler:
    """Handles all user input operations. Part of the frontend layer."""

    @staticmethod
    def get_command() -> str:
        """Get a command from user."""
        return input("\n> ").strip()

    @staticmethod
    def get_amount() -> Optional[float]:
        """Get a valid amount from user."""
        try:
            amount_str = input("Enter amount: ").strip()
            amount = float(amount_str)
            if amount <= 0:
                print("\n[!]Amount must be positive")
                return None
            return amount
        except ValueError:
            print("\n[!]Invalid amount. Please enter a number.")
            return None

    @staticmethod
    def get_category(
        categories: List[str], transaction_type_name: str
    ) -> Optional[str]:
        """Get a category from user, with option to add new.

        Args:
            categories: Sorted list of category names.
            transaction_type_name: 'Income' or 'Expense' for display.
        """
        print(f"\n[*] Available {transaction_type_name} Categories:")
        for i, cat in enumerate(categories, 1):
            print(f"   {i}. {cat}")
        print(f"   {len(categories) + 1}. [Add new category]")

        choice = input("Select category (number or name): ").strip()

        try:
            choice_num = int(choice)
            if 1 <= choice_num <= len(categories):
                return categories[choice_num - 1]
            elif choice_num == len(categories) + 1:
                new_category = input("Enter new category name: ").strip()
                if new_category:
                    return new_category
                print("\n[!]Category name cannot be empty")
                return None
            else:
                print("\n[!]Invalid selection")
                return None
        except ValueError:
            if choice in categories:
                return choice
            confirm = (
                input(f"Category '{choice}' doesn't exist. Add it? (y/n): ")
                .strip()
                .lower()
            )
            if confirm == "y":
                return choice
            return None

    @staticmethod
    def get_description() -> str:
        """Get an optional description from user."""
        return input("Enter description (optional): ").strip()

    @staticmethod
    def get_datetime() -> Optional[str]:
        """Get datetime from user, defaulting to now. Returns ISO string or None for now."""
        date_str = input("Enter date (YYYY-MM-DD) or press Enter for today: ").strip()

        if not date_str:
            return None  # caller will use current time

        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            return dt.isoformat()
        except ValueError:
            print("\n[i]Invalid date format. Using current date.")
            return None

    @staticmethod
    def get_transaction_input(
        transaction_type_name: str,
        categories: List[str],
    ) -> Optional[Dict]:
        """Get all inputs for a new transaction step by step.

        Returns dict with keys: amount, category, description, date (ISO str or None).
        """
        print(f"\n{'=' * 50}")
        print(f"  New {transaction_type_name} Transaction")
        print("=" * 50)

        amount = InputHandler.get_amount()
        if amount is None:
            return None

        category = InputHandler.get_category(categories, transaction_type_name)
        if category is None:
            return None

        description = InputHandler.get_description()
        date = InputHandler.get_datetime()

        return {
            "amount": amount,
            "category": category,
            "description": description,
            "date": date,
        }

    @staticmethod
    def get_edit_input(current: Dict, categories: List[str]) -> Optional[Dict]:
        """Get inputs for editing a transaction.

        Args:
            current: Dict with current transaction data (from serialisation).
            categories: Available categories.

        Returns dict with updated values.
        """
        print(f"\n{'=' * 50}")
        print("  Edit Transaction")
        print("=" * 50)
        print("\n[i]Press Enter to keep current value")

        print(f"\nCurrent values:")
        print(f"   Amount: {current['sign']}{abs(current['amount']):.2f}")
        print(f"   Category: {current['category']}")
        print(f"   Description: {current['description'] or 'N/A'}")
        print(f"   Date: {current['date']}")
        print()

        # Amount
        amount_str = input(f"Amount [{current['amount']}]: ").strip()
        if amount_str:
            try:
                amount = float(amount_str)
                if amount <= 0:
                    print("\n[!]Amount must be positive")
                    return None
            except ValueError:
                print("\n[!]Invalid amount")
                return None
        else:
            amount = current["amount"]

        # Category
        if current.get("is_transfer"):
            category = current["category"]
        else:
            print(f"\nCurrent category: {current['category']}")
            change_cat = input("Change category? (y/n): ").strip().lower()
            if change_cat == "y":
                type_name = (
                    "Income" if current["transaction_type"] == "+" else "Expense"
                )
                category = InputHandler.get_category(categories, type_name)
                if category is None:
                    return None
            else:
                category = current["category"]

        # Description
        desc_input = input(f"Description [{current['description'] or 'N/A'}]: ").strip()
        description = desc_input if desc_input else current["description"]

        # Date
        date_str = input(f"Date [{current['date']}]: ").strip()
        if date_str:
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                date = dt.isoformat()
            except ValueError:
                print("\n[i]Invalid date format. Keeping current date.")
                date = current["date"]
        else:
            date = current["date"]

        return {
            "amount": amount,
            "category": category,
            "description": description,
            "date": date,
        }

    @staticmethod
    def get_transfer_edit_input(current: Dict) -> Optional[Dict]:
        """Get inputs for editing a transfer transaction."""
        print(f"\n{'=' * 50}")
        print("  Edit Transfer")
        print("=" * 50)
        print("\n[i]Press Enter to keep current value")
        print("\n[i]Note: Transfer category and wallets cannot be changed")

        print(f"\nCurrent values:")
        print(f"   Amount: {current['sign']}{abs(current['amount']):.2f}")
        print(f"   From: {current.get('from_wallet', '?')}")
        print(f"   To: {current.get('to_wallet', '?')}")
        print(f"   Description: {current['description'] or 'N/A'}")
        print(f"   Date: {current['date']}")
        print()

        # Amount
        amount_str = input(f"Amount [{current['amount']}]: ").strip()
        if amount_str:
            try:
                amount = float(amount_str)
                if amount <= 0:
                    print("\n[!]Amount must be positive")
                    return None
            except ValueError:
                print("\n[!]Invalid amount")
                return None
        else:
            amount = current["amount"]

        # Description
        desc_input = input(f"Description [{current['description'] or 'N/A'}]: ").strip()
        description = desc_input if desc_input else current["description"]

        # Date
        date_str = input(f"Date [{current['date']}]: ").strip()
        if date_str:
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                date = dt.isoformat()
            except ValueError:
                print("\n[i]Invalid date format. Keeping current date.")
                date = current["date"]
        else:
            date = current["date"]

        return {
            "amount": amount,
            "description": description,
            "date": date,
        }

    @staticmethod
    def confirm(message: str) -> bool:
        """Get a yes/no confirmation from user."""
        response = input(f"{message} (y/n): ").strip().lower()
        return response == "y"

    @staticmethod
    def parse_indexed_command(command: str) -> Tuple[Optional[str], Optional[int]]:
        """Parse commands like 'show 1', 'edit 2', 'delete 3'."""
        parts = command.split()
        if len(parts) != 2:
            return None, None

        action = parts[0]
        try:
            index = int(parts[1])
            return action, index
        except ValueError:
            return None, None

    @staticmethod
    def parse_named_command(command: str) -> Tuple[Optional[str], Optional[str]]:
        """Parse commands like 'wallet Main', 'switch Savings'."""
        parts = command.split(maxsplit=1)
        if len(parts) != 2:
            return None, None
        return parts[0], parts[1]

    # ============= Wallet Input Methods =============

    @staticmethod
    def get_wallet_type() -> Optional[str]:
        """Get wallet type from user. Returns 'regular' or 'deposit'."""
        print("\n[*] Wallet Types:")
        print("   1. Regular - Standard wallet for daily transactions")
        print("   2. Deposit - Savings with interest rate and maturity date")

        choice = input("Select wallet type (1/2): ").strip()

        if choice == "1":
            return "regular"
        elif choice == "2":
            return "deposit"
        else:
            print("\n[!]Invalid selection")
            return None

    @staticmethod
    def get_wallet_input() -> Optional[Dict]:
        """Get all inputs for a new wallet step by step."""
        print(f"\n{'=' * 50}")
        print("  New Wallet")
        print("=" * 50)

        wallet_type = InputHandler.get_wallet_type()
        if wallet_type is None:
            return None

        name = input("Enter wallet name: ").strip()
        if not name:
            print("\n[!]Wallet name cannot be empty")
            return None

        currency = input("Enter currency (default: KZT): ").strip()
        if not currency:
            currency = "KZT"

        starting_str = input("Enter starting balance (default: 0): ").strip()
        starting_value = None
        if starting_str:
            try:
                starting_value = float(starting_str)
            except ValueError:
                print("\n[i]Invalid amount. Starting with 0.")

        description = input("Enter description (optional): ").strip()

        result = {
            "name": name,
            "currency": currency,
            "starting_value": starting_value,
            "description": description,
            "wallet_type": wallet_type,
        }

        if wallet_type == "deposit":
            deposit_data = InputHandler.get_deposit_input()
            if deposit_data is None:
                return None
            result.update(deposit_data)

        return result

    @staticmethod
    def get_deposit_input() -> Optional[Dict]:
        """Get deposit-specific inputs."""
        print("\n--- Deposit Settings ---")

        rate_str = input("Enter annual interest rate (e.g., 12.5 for 12.5%): ").strip()
        try:
            interest_rate = float(rate_str)
            if interest_rate <= 0:
                print("\n[!]Interest rate must be positive")
                return None
        except ValueError:
            print("\n[!]Invalid interest rate")
            return None

        term_str = input("Enter term in months: ").strip()
        try:
            term_months = int(term_str)
            if term_months <= 0:
                print("\n[!]Term must be positive")
                return None
        except ValueError:
            print("\n[!]Invalid term")
            return None

        cap_choice = (
            input("Enable interest capitalization? (y/n, default: n): ").strip().lower()
        )
        capitalization = cap_choice == "y"

        return {
            "interest_rate": interest_rate,
            "term_months": term_months,
            "capitalization": capitalization,
        }

    @staticmethod
    def get_wallet_edit_input(wallet_data: Dict) -> Optional[Dict]:
        """Get inputs for editing a wallet.

        Args:
            wallet_data: Dict with current wallet data (from serialisation).
        """
        print(f"\n{'=' * 50}")
        print("  Edit Wallet")
        print("=" * 50)
        print("\n[i]Press Enter to keep current value")

        print(f"\nCurrent values:")
        print(f"   Name:        {wallet_data['name']}")
        print(f"   Currency:    {wallet_data['currency']}")
        print(f"   Description: {wallet_data['description'] or 'N/A'}")
        print()

        new_name = input(f"Name [{wallet_data['name']}]: ").strip()
        if not new_name:
            new_name = wallet_data["name"]

        new_currency = input(f"Currency [{wallet_data['currency']}]: ").strip()
        if not new_currency:
            new_currency = wallet_data["currency"]

        new_desc = input(
            f"Description [{wallet_data['description'] or 'N/A'}]: "
        ).strip()
        if not new_desc:
            new_desc = wallet_data["description"]

        return {
            "new_name": new_name if new_name != wallet_data["name"] else None,
            "currency": (
                new_currency if new_currency != wallet_data["currency"] else None
            ),
            "description": new_desc,
        }

    @staticmethod
    def get_transfer_input(
        from_wallet: Dict, target_wallets: List[Dict]
    ) -> Optional[Dict]:
        """Get all inputs for a new transfer.

        Args:
            from_wallet: Dict with current wallet data.
            target_wallets: List of dicts with available target wallets.
        """
        print(f"\n{'=' * 50}")
        print("  New Transfer")
        print("=" * 50)

        if not target_wallets:
            print(
                "\n[!]No other wallets available for transfer. "
                "Create another wallet first."
            )
            return None

        print(f"\nTransferring FROM: {from_wallet['name']} ({from_wallet['currency']})")
        print(f"Available balance: {from_wallet['balance']:.2f}")
        print("\nSelect target wallet:")
        for i, w in enumerate(target_wallets, 1):
            print(
                f"   {i}. {w['name']} ({w['currency']}) "
                f"- Balance: {w['balance']:.2f}"
            )

        choice = input("\nSelect wallet (number): ").strip()
        try:
            choice_num = int(choice)
            if 1 <= choice_num <= len(target_wallets):
                target = target_wallets[choice_num - 1]
            else:
                print("\n[!]Invalid selection")
                return None
        except ValueError:
            print("\n[!]Invalid selection")
            return None

        amount = InputHandler.get_amount()
        if amount is None:
            return None

        description = InputHandler.get_description()
        date = InputHandler.get_datetime()

        return {
            "target_wallet_name": target["name"],
            "amount": amount,
            "description": description,
            "date": date,
        }

    # ============= Filter Input Methods =============

    @staticmethod
    def get_date_filter() -> Optional[Dict]:
        """Get a date filter from user selection. Returns filter dict."""
        print("\n[*] Date Filter Options:")
        print("   1. Today")
        print("   2. Last Week")
        print("   3. Last Month")
        print("   4. This Month")
        print("   5. Last Year")
        print("   6. This Year")
        print("   7. Custom Date Range")
        print("   0. Cancel")
        choice = input("Select option: ").strip()

        filter_map = {
            "1": "today",
            "2": "last_week",
            "3": "last_month",
            "4": "this_month",
            "5": "last_year",
            "6": "this_year",
        }

        if choice == "0":
            return None
        elif choice in filter_map:
            return {"filter_type": filter_map[choice]}
        elif choice == "7":
            return InputHandler.get_custom_date_range()
        else:
            print("\n[!]Invalid option")
            return None

    @staticmethod
    def get_custom_date_range() -> Optional[Dict]:
        """Get a custom date range from user."""
        print("\nEnter date range (YYYY-MM-DD format):")
        print("Press Enter to leave a bound open")

        start_str = input("Start date (or Enter for no start): ").strip()
        end_str = input("End date (or Enter for no end): ").strip()

        start_date = None
        end_date = None

        if start_str:
            try:
                start_date = datetime.strptime(start_str, "%Y-%m-%d").isoformat()
            except ValueError:
                print("\n[!]Invalid start date format")
                return None

        if end_str:
            try:
                end_date = (
                    datetime.strptime(end_str, "%Y-%m-%d")
                    .replace(hour=23, minute=59, second=59)
                    .isoformat()
                )
            except ValueError:
                print("\n[!]Invalid end date format")
                return None

        if not start_date and not end_date:
            print("\n[i]No date range specified")
            return None

        return {
            "filter_type": "date_range",
            "start_date": start_date,
            "end_date": end_date,
        }

    @staticmethod
    def get_type_filter() -> Optional[Dict]:
        """Get a transaction type filter from user selection."""
        print("\n[*] Transaction Type Filter Options:")
        print("   1. Income Only")
        print("   2. Expense Only")
        print("   3. Transfers Only")
        print("   4. No Transfers")
        print("   5. Recurring Only")
        print("   6. Non-Recurring Only")
        print("   0. Cancel")
        choice = input("Select option: ").strip()

        if choice == "0":
            return None
        elif choice == "1":
            inc = InputHandler.confirm("Include incoming transfers?")
            return {"filter_type": "income_only", "include_transfers": inc}
        elif choice == "2":
            inc = InputHandler.confirm("Include outgoing transfers?")
            return {"filter_type": "expense_only", "include_transfers": inc}
        elif choice == "3":
            return {"filter_type": "transfers_only"}
        elif choice == "4":
            return {"filter_type": "no_transfers"}
        elif choice == "5":
            return {"filter_type": "recurring_only"}
        elif choice == "6":
            return {"filter_type": "non_recurring"}
        else:
            print("\n[!]Invalid option")
            return None

    @staticmethod
    def get_category_filter(available_categories: List[str]) -> Optional[Dict]:
        """Get a category filter from user."""
        if not available_categories:
            print("\n[!]No categories available")
            return None

        print("\n[*] Filter Mode:")
        print("   1. Include only selected categories")
        print("   2. Exclude selected categories")
        print("   0. Cancel")

        mode_choice = input("Select mode: ").strip()
        if mode_choice == "0":
            return None
        elif mode_choice == "1":
            mode = "include"
        elif mode_choice == "2":
            mode = "exclude"
        else:
            print("\n[!]Invalid option")
            return None

        sorted_cats = sorted(available_categories)
        print("\n[*] Available Categories:")
        for i, cat in enumerate(sorted_cats, 1):
            print(f"   {i}. {cat}")

        print("\nEnter category numbers separated by commas (e.g., 1,3,5):")
        selection = input("Selection: ").strip()

        if not selection:
            print("\n[i]No categories selected")
            return None

        selected = []
        try:
            indices = [int(x.strip()) for x in selection.split(",")]
            for idx in indices:
                if 1 <= idx <= len(sorted_cats):
                    selected.append(sorted_cats[idx - 1])
                else:
                    print(f"\n[!]Invalid index: {idx}")
                    return None
        except ValueError:
            print("\n[!]Invalid input. Use numbers separated by commas.")
            return None

        if not selected:
            print("\n[i]No valid categories selected")
            return None

        return {"filter_type": "category", "categories": selected, "mode": mode}

    @staticmethod
    def get_amount_filter() -> Optional[Dict]:
        """Get an amount filter from user selection."""
        print("\n[*] Amount Filter Options:")
        print("   1. Large Transactions")
        print("   2. Small Transactions")
        print("   3. Custom Amount Range")
        print("   0. Cancel")
        choice = input("Select option: ").strip()

        if choice == "0":
            return None
        elif choice == "1":
            threshold = input("Enter minimum amount (default 10000): ").strip()
            try:
                threshold = float(threshold) if threshold else 10000
                return {"filter_type": "large", "threshold": threshold}
            except ValueError:
                print("\n[!]Invalid amount")
                return None
        elif choice == "2":
            threshold = input("Enter maximum amount (default 100): ").strip()
            try:
                threshold = float(threshold) if threshold else 100
                return {"filter_type": "small", "threshold": threshold}
            except ValueError:
                print("\n[!]Invalid amount")
                return None
        elif choice == "3":
            return InputHandler.get_custom_amount_range()
        else:
            print("\n[!]Invalid option")
            return None

    @staticmethod
    def get_custom_amount_range() -> Optional[Dict]:
        """Get a custom amount range from user."""
        print("\nEnter amount range:")
        print("Press Enter to leave a bound open")

        min_str = input("Minimum amount (or Enter for no minimum): ").strip()
        max_str = input("Maximum amount (or Enter for no maximum): ").strip()

        min_amount = None
        max_amount = None

        if min_str:
            try:
                min_amount = float(min_str)
                if min_amount < 0:
                    print("\n[!]Amount cannot be negative")
                    return None
            except ValueError:
                print("\n[!]Invalid minimum amount")
                return None

        if max_str:
            try:
                max_amount = float(max_str)
                if max_amount < 0:
                    print("\n[!]Amount cannot be negative")
                    return None
            except ValueError:
                print("\n[!]Invalid maximum amount")
                return None

        if min_amount and max_amount and min_amount > max_amount:
            print("\n[!]Minimum cannot be greater than maximum")
            return None

        if min_amount is None and max_amount is None:
            print("\n[i]No amount range specified")
            return None

        return {
            "filter_type": "amount_range",
            "min_amount": min_amount,
            "max_amount": max_amount,
        }

    @staticmethod
    def get_description_filter() -> Optional[Dict]:
        """Get a description search filter from user."""
        search_term = input("Enter search term: ").strip()
        if not search_term:
            print("\n[i]No search term provided")
            return None

        case_sensitive = InputHandler.confirm("Case sensitive search?")
        return {
            "filter_type": "description",
            "search_term": search_term,
            "case_sensitive": case_sensitive,
        }

    @staticmethod
    def get_filter_to_remove(filters: List[Dict]) -> Optional[int]:
        """Get the index of a filter to remove.

        Args:
            filters: List of filter dicts with 'name' and 'description' keys.
        """
        if not filters:
            print("\n[i]No active filters to remove")
            return None

        print("\n[?] Active Filters:")
        for i, f in enumerate(filters, 1):
            print(f"   {i}. {f['name']}: {f['description']}")

        choice = input("Enter filter number to remove (0 to cancel): ").strip()

        try:
            idx = int(choice)
            if idx == 0:
                return None
            if 1 <= idx <= len(filters):
                return idx - 1
            print("\n[!]Invalid filter number")
            return None
        except ValueError:
            print("\n[!]Invalid input")
            return None

    # ============= Recurrence Input Methods =============

    @staticmethod
    def _get_interval(unit: str) -> int:
        """Get the recurrence interval from user."""
        interval_str = input(f"Every how many {unit}? (default: 1): ").strip()
        if not interval_str:
            return 1
        try:
            interval = int(interval_str)
            if interval < 1:
                print("\n[!]Interval must be at least 1. Using 1.")
                return 1
            return interval
        except ValueError:
            print("\n[i]Invalid input. Using 1.")
            return 1

    @staticmethod
    def _get_weekdays() -> List[int]:
        """Get weekday selection from user. Returns list of weekday ints (0=Mon)."""
        print("\nSelect days (comma-separated numbers):")
        print("   1. Monday    2. Tuesday   3. Wednesday  4. Thursday")
        print("   5. Friday    6. Saturday  7. Sunday")
        selection = input("Days: ").strip()
        if not selection:
            return []

        weekdays = []
        try:
            nums = [int(x.strip()) for x in selection.split(",")]
            for n in nums:
                if 1 <= n <= 7:
                    weekdays.append(n - 1)  # Convert to 0-based (Mon=0)
                else:
                    print(f"\n[!]Invalid day number: {n}")
        except ValueError:
            print("\n[!]Invalid input. Use numbers separated by commas.")
        return weekdays

    @staticmethod
    def _get_month_weekday() -> Tuple[Optional[int], Optional[int]]:
        """Get 'Nth weekday of month' from user.
        Returns (week_number, weekday_int) or (None, None).
        """
        print("\nWhich occurrence? (e.g., 1st Monday)")
        week_str = input("Week number (1-5): ").strip()
        try:
            week = int(week_str)
            if not 1 <= week <= 5:
                print("\n[!]Must be between 1 and 5")
                return None, None
        except ValueError:
            print("\n[!]Invalid input")
            return None, None

        print("Which day?")
        print("   1. Monday    2. Tuesday   3. Wednesday  4. Thursday")
        print("   5. Friday    6. Saturday  7. Sunday")
        day_str = input("Day: ").strip()
        try:
            day = int(day_str)
            if 1 <= day <= 7:
                return week, day - 1  # 0-based weekday
            print("\n[!]Invalid day number")
            return None, None
        except ValueError:
            print("\n[!]Invalid input")
            return None, None

    @staticmethod
    def _get_end_condition() -> Dict:
        """Get end condition from user. Returns dict for recurrence rule."""
        print("\nEnd Condition:")
        print("   1. Never")
        print("   2. On a specific date")
        print("   3. After N occurrences")
        choice = input("Select (default: 1): ").strip()

        if choice == "2":
            date_str = input("End date (YYYY-MM-DD): ").strip()
            try:
                end_date = datetime.strptime(date_str, "%Y-%m-%d")
                return {"end_condition": "on_date", "end_date": end_date.isoformat()}
            except ValueError:
                print("\n[i]Invalid date. Setting to 'Never'.")
                return {"end_condition": "never"}
        elif choice == "3":
            count_str = input("Number of occurrences: ").strip()
            try:
                count = int(count_str)
                if count > 0:
                    return {
                        "end_condition": "after_count",
                        "max_occurrences": count,
                    }
                else:
                    print("\n[i]Must be positive. Setting to 'Never'.")
            except ValueError:
                print("\n[i]Invalid input. Setting to 'Never'.")

        return {"end_condition": "never"}

    @staticmethod
    def _get_custom_recurrence() -> Optional[Dict]:
        """Get a fully custom recurrence rule from user."""
        print("\nCustom Recurrence:")
        print("   1. Daily")
        print("   2. Weekly")
        print("   3. Monthly")
        print("   4. Yearly")
        freq_choice = input("Select frequency: ").strip()

        rule = {}

        if freq_choice == "1":
            interval = InputHandler._get_interval("days")
            rule = {"frequency": "daily", "interval": interval}
        elif freq_choice == "2":
            interval = InputHandler._get_interval("weeks")
            weekdays = InputHandler._get_weekdays()
            rule = {
                "frequency": "weekly",
                "interval": interval,
                "weekdays": weekdays,
            }
        elif freq_choice == "3":
            interval = InputHandler._get_interval("months")
            print("\nMonthly pattern:")
            print("   1. Same day of month")
            print("   2. Nth weekday (e.g., 1st Monday)")
            pattern = input("Select (default: 1): ").strip()
            if pattern == "2":
                week, weekday = InputHandler._get_month_weekday()
                if week is None:
                    return None
                rule = {
                    "frequency": "monthly",
                    "interval": interval,
                    "month_week": week,
                    "month_weekday": weekday,
                }
            else:
                rule = {"frequency": "monthly", "interval": interval}
        elif freq_choice == "4":
            interval = InputHandler._get_interval("years")
            rule = {"frequency": "yearly", "interval": interval}
        else:
            print("\n[!]Invalid selection")
            return None

        end_data = InputHandler._get_end_condition()
        rule.update(end_data)
        return rule

    @staticmethod
    def get_recurrence_rule_input() -> Optional[Dict]:
        """Get a recurrence rule from user via menu selection.
        Returns dict describing the rule.
        """
        print("\nRecurrence Pattern:")
        print("   1. Daily")
        print("   2. Weekly")
        print("   3. Monthly")
        print("   4. Yearly")
        print("   5. Every Weekday (Mon-Fri)")
        print("   6. Custom")
        print("   0. Cancel")
        choice = input("Select pattern: ").strip()

        if choice == "0":
            return None

        rule = {}
        if choice == "1":
            rule = {"frequency": "daily", "interval": 1}
        elif choice == "2":
            weekdays = InputHandler._get_weekdays()
            rule = {"frequency": "weekly", "interval": 1, "weekdays": weekdays}
        elif choice == "3":
            print("\nMonthly pattern:")
            print("   1. Same day of month")
            print("   2. Nth weekday (e.g., 1st Monday)")
            pattern = input("Select (default: 1): ").strip()
            if pattern == "2":
                week, weekday = InputHandler._get_month_weekday()
                if week is None:
                    return None
                rule = {
                    "frequency": "monthly",
                    "interval": 1,
                    "month_week": week,
                    "month_weekday": weekday,
                }
            else:
                rule = {"frequency": "monthly", "interval": 1}
        elif choice == "4":
            rule = {"frequency": "yearly", "interval": 1}
        elif choice == "5":
            rule = {
                "frequency": "weekly",
                "interval": 1,
                "weekdays": [0, 1, 2, 3, 4],  # Mon-Fri
            }
        elif choice == "6":
            return InputHandler._get_custom_recurrence()
        else:
            print("\n[!]Invalid selection")
            return None

        end_data = InputHandler._get_end_condition()
        rule.update(end_data)
        return rule

    @staticmethod
    def get_recurring_transaction_input(
        transaction_type_name: str,
        categories: List[str],
    ) -> Optional[Dict]:
        """Get all inputs for a new recurring transaction.
        Returns dict with transaction data + recurrence_rule dict.
        """
        print(f"\n{'=' * 50}")
        print(f"  New Recurring {transaction_type_name}")
        print("=" * 50)

        amount = InputHandler.get_amount()
        if amount is None:
            return None

        category = InputHandler.get_category(categories, transaction_type_name)
        if category is None:
            return None

        description = InputHandler.get_description()

        print("\nStart date for recurrence:")
        start_date = InputHandler.get_datetime()

        rule = InputHandler.get_recurrence_rule_input()
        if rule is None:
            return None

        return {
            "amount": amount,
            "category": category,
            "description": description,
            "start_date": start_date,
            "recurrence_rule": rule,
        }

    @staticmethod
    def get_recurring_edit_input(
        recurring_data: Dict, categories: List[str]
    ) -> Optional[Dict]:
        """Get edit inputs for a recurring transaction.

        Args:
            recurring_data: Dict with current recurring data (from serialisation).
            categories: Available categories.
        """
        print(f"\n{'=' * 50}")
        print("  Edit Recurring Transaction")
        print("=" * 50)
        print(f"\nCurrent details:")
        print(recurring_data["detail"])

        print("\nEdit Options:")
        active_label = "Pause" if recurring_data["is_active"] else "Resume"
        print("   1. Edit template (affects future occurrences)")
        print("   2. Skip a specific future date")
        print(f"   3. {active_label}")
        print("   0. Cancel")
        choice = input("Select option: ").strip()

        if choice == "0":
            return None
        elif choice == "1":
            return InputHandler._get_recurring_template_edit(recurring_data, categories)
        elif choice == "2":
            return InputHandler._get_recurring_skip_date()
        elif choice == "3":
            return {"edit_action": "toggle_active"}
        else:
            print("\n[!]Invalid option")
            return None

    @staticmethod
    def _get_recurring_template_edit(
        recurring_data: Dict, categories: List[str]
    ) -> Optional[Dict]:
        """Get template field edits for a recurring transaction."""
        print("\n[i]Press Enter to keep current value")

        amount_str = input(f"Amount [{recurring_data['amount']}]: ").strip()
        if amount_str:
            try:
                amount = float(amount_str)
                if amount <= 0:
                    print("\n[!]Amount must be positive")
                    return None
            except ValueError:
                print("\n[!]Invalid amount")
                return None
        else:
            amount = recurring_data["amount"]

        print(f"\nCurrent category: {recurring_data['category']}")
        change_cat = input("Change category? (y/n): ").strip().lower()
        if change_cat == "y":
            type_name = (
                "Income" if recurring_data["transaction_type"] == "+" else "Expense"
            )
            category = InputHandler.get_category(categories, type_name)
            if category is None:
                return None
        else:
            category = recurring_data["category"]

        desc_input = input(
            f"Description [{recurring_data['description'] or 'N/A'}]: "
        ).strip()
        description = desc_input if desc_input else recurring_data["description"]

        return {
            "edit_action": "edit_template",
            "amount": amount,
            "category": category,
            "description": description,
        }

    @staticmethod
    def _get_recurring_skip_date() -> Optional[Dict]:
        """Get a date to skip for a recurring transaction."""
        date_str = input("Enter date to skip (YYYY-MM-DD): ").strip()
        try:
            skip_date = datetime.strptime(date_str, "%Y-%m-%d")
            return {"edit_action": "skip_date", "date": skip_date.isoformat()}
        except ValueError:
            print("\n[!]Invalid date format")
            return None

    @staticmethod
    def get_recurring_delete_option() -> Optional[int]:
        """Get deletion scope for a recurring transaction."""
        print("\nDelete Options:")
        print("   1. Delete template only (keep generated transactions)")
        print("   2. Delete template + future generated transactions")
        print("   3. Delete template + ALL generated transactions")
        print("   0. Cancel")
        choice = input("Select option: ").strip()

        if choice in ("0", "1", "2", "3"):
            return int(choice)
        print("\n[!]Invalid option")
        return None
