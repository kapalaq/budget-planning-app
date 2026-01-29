"""Input handling utilities for the budget planner."""
from datetime import datetime
from typing import Optional, Tuple, Set, Dict, List, TYPE_CHECKING
from models.transaction import Transaction, TransactionType
from models.recurrence import (
    RecurrenceRule,
    RecurringTransaction,
    Frequency,
    Weekday,
    EndCondition,
    WEEKDAY_NAMES,
)
from ui.display import Display
from wallet.wallet import Wallet, WalletType
from strategies.filtering import (
    FilterStrategy,
    FilteringContext,
    TodayFilter,
    LastWeekFilter,
    LastMonthFilter,
    ThisMonthFilter,
    LastYearFilter,
    ThisYearFilter,
    DateRangeFilter,
    IncomeOnlyFilter,
    ExpenseOnlyFilter,
    TransferOnlyFilter,
    NoTransfersFilter,
    RecurringOnlyFilter,
    NonRecurringFilter,
    CategoryFilter,
    AmountRangeFilter,
    LargeTransactionsFilter,
    SmallTransactionsFilter,
    DescriptionFilter,
)

if TYPE_CHECKING:
    from wallet.wallet_manager import WalletManager


class InputHandler:
    """Handles all user input operations."""
    
    @staticmethod
    def get_command() -> str:
        """Get a command from user."""
        return input("\n> ").strip().lower()
    
    @staticmethod
    def get_amount() -> Optional[float]:
        """Get a valid amount from user."""
        try:
            amount_str = input("Enter amount: ").strip()
            amount = float(amount_str)
            if amount <= 0:
                Display.show_error("Amount must be positive")
                return None
            return amount
        except ValueError:
            Display.show_error("Invalid amount. Please enter a number.")
            return None
    
    @staticmethod
    def get_category(categories: Set[str], transaction_type: TransactionType) -> Optional[str]:
        """Get a category from user, with option to add new."""
        type_name = "Income" if transaction_type == TransactionType.INCOME else "Expense"
        Display.show_categories(categories, type_name)
        
        sorted_categories = sorted(categories)
        choice = input("Select category (number or name): ").strip()
        
        # Check if it's a number
        try:
            choice_num = int(choice)
            if 1 <= choice_num <= len(sorted_categories):
                return sorted_categories[choice_num - 1]
            elif choice_num == len(sorted_categories) + 1:
                # Add new category
                new_category = input("Enter new category name: ").strip()
                if new_category:
                    return new_category
                Display.show_error("Category name cannot be empty")
                return None
            else:
                Display.show_error("Invalid selection")
                return None
        except ValueError:
            # It's a name - check if it exists or add it
            if choice in categories:
                return choice
            # Ask if they want to add it
            confirm = input(f"Category '{choice}' doesn't exist. Add it? (y/n): ").strip().lower()
            if confirm == 'y':
                return choice
            return None
    
    @staticmethod
    def get_description() -> str:
        """Get an optional description from user."""
        return input("Enter description (optional): ").strip()
    
    @staticmethod
    def get_datetime() -> datetime:
        """Get datetime from user, defaulting to now."""
        date_str = input("Enter date (YYYY-MM-DD) or press Enter for today: ").strip()
        
        if not date_str:
            return datetime.now()
        
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            Display.show_info("Invalid date format. Using current date.")
            return datetime.now()
    
    @staticmethod
    def get_transaction_input(
        transaction_type: TransactionType,
        categories: Set[str]
    ) -> Optional[Transaction]:
        """Get all inputs for a new transaction step by step."""
        type_name = "Income" if transaction_type == TransactionType.INCOME else "Expense"
        Display.show_header(f"New {type_name} Transaction")
        
        # Step 1: Amount
        amount = InputHandler.get_amount()
        if amount is None:
            return None
        
        # Step 2: Category
        category = InputHandler.get_category(categories, transaction_type)
        if category is None:
            return None
        
        # Step 3: Description
        description = InputHandler.get_description()
        
        # Step 4: Date
        date = InputHandler.get_datetime()
        
        return Transaction(
            amount=amount,
            transaction_type=transaction_type,
            category=category,
            description=description,
            datetime_created=date
        )
    
    @staticmethod
    def get_edit_input(
        transaction: Transaction,
        categories: Set[str]
    ) -> Optional[Transaction]:
        """Get inputs for editing a transaction."""
        Display.show_header("Edit Transaction")
        Display.show_info("Press Enter to keep current value")
        
        print(f"\nCurrent values:")
        print(transaction.detailed_str())
        print()
        
        # Amount
        amount_str = input(f"Amount [{transaction.amount}]: ").strip()
        if amount_str:
            try:
                amount = float(amount_str)
                if amount <= 0:
                    Display.show_error("Amount must be positive")
                    return None
            except ValueError:
                Display.show_error("Invalid amount")
                return None
        else:
            amount = transaction.amount
        
        # Category
        print(f"\nCurrent category: {transaction.category}")
        change_cat = input("Change category? (y/n): ").strip().lower()
        if change_cat == 'y':
            category = InputHandler.get_category(categories, transaction.transaction_type)
            if category is None:
                return None
        else:
            category = transaction.category
        
        # Description
        desc_input = input(f"Description [{transaction.description or 'N/A'}]: ").strip()
        description = desc_input if desc_input else transaction.description
        
        # Date
        current_date = transaction.datetime_created.strftime("%Y-%m-%d")
        date_str = input(f"Date [{current_date}]: ").strip()
        if date_str:
            try:
                date = datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                Display.show_info("Invalid date format. Keeping current date.")
                date = transaction.datetime_created
        else:
            date = transaction.datetime_created
        
        return Transaction(
            amount=amount,
            transaction_type=transaction.transaction_type,
            category=category,
            description=description,
            datetime_created=date
        )
    
    @staticmethod
    def confirm(message: str) -> bool:
        """Get a yes/no confirmation from user."""
        response = input(f"{message} (y/n): ").strip().lower()
        return response == 'y'
    
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

    @staticmethod
    def get_wallet_type() -> Optional[WalletType]:
        """Get wallet type from user."""
        print("\n📁 Wallet Types:")
        print("   1. Regular - Standard wallet for daily transactions")
        print("   2. Deposit - Savings with interest rate and maturity date")

        choice = input("Select wallet type (1/2): ").strip()

        if choice == "1":
            return WalletType.REGULAR
        elif choice == "2":
            return WalletType.DEPOSIT
        else:
            Display.show_error("Invalid selection")
            return None

    @staticmethod
    def get_wallet_input() -> Optional[Dict]:
        """Get all inputs for a new wallet step by step."""
        Display.show_header("New Wallet")

        # Step 1: Wallet type
        wallet_type = InputHandler.get_wallet_type()
        if wallet_type is None:
            return None

        # Step 2: Name (required)
        name = input("Enter wallet name: ").strip()
        if not name:
            Display.show_error("Wallet name cannot be empty")
            return None

        # Step 3: Currency
        currency = input("Enter currency (default: KZT): ").strip()
        if not currency:
            currency = "KZT"

        # Step 4: Starting balance
        starting_str = input("Enter starting balance (default: 0): ").strip()
        starting_value = None
        if starting_str:
            try:
                starting_value = float(starting_str)
            except ValueError:
                Display.show_info("Invalid amount. Starting with 0.")

        # Step 5: Description
        description = input("Enter description (optional): ").strip()

        result = {
            "name": name,
            "currency": currency,
            "starting_value": starting_value,
            "description": description,
            "wallet_type": wallet_type,
        }

        # Step 6: Deposit-specific inputs
        if wallet_type == WalletType.DEPOSIT:
            deposit_data = InputHandler.get_deposit_input()
            if deposit_data is None:
                return None
            result.update(deposit_data)

        return result

    @staticmethod
    def get_deposit_input() -> Optional[Dict]:
        """Get deposit-specific inputs."""
        print("\n--- Deposit Settings ---")

        # Interest rate
        rate_str = input("Enter annual interest rate (e.g., 12.5 for 12.5%): ").strip()
        try:
            interest_rate = float(rate_str)
            if interest_rate <= 0:
                Display.show_error("Interest rate must be positive")
                return None
        except ValueError:
            Display.show_error("Invalid interest rate")
            return None

        # Term in months
        term_str = input("Enter term in months: ").strip()
        try:
            term_months = int(term_str)
            if term_months <= 0:
                Display.show_error("Term must be positive")
                return None
        except ValueError:
            Display.show_error("Invalid term")
            return None

        # Capitalization
        cap_choice = input("Enable interest capitalization? (y/n, default: n): ").strip().lower()
        capitalization = cap_choice == 'y'

        return {
            "interest_rate": interest_rate,
            "term_months": term_months,
            "capitalization": capitalization,
        }

    @staticmethod
    def get_wallet_edit_input(wallet: Wallet) -> Optional[Dict]:
        """Get inputs for editing a wallet."""
        Display.show_header("Edit Wallet")
        Display.show_info("Press Enter to keep current value")

        print(f"\nCurrent values:")
        print(f"   Name:        {wallet.name}")
        print(f"   Currency:    {wallet.currency}")
        print(f"   Description: {wallet.description or 'N/A'}")
        print()

        # Name
        new_name = input(f"Name [{wallet.name}]: ").strip()
        if not new_name:
            new_name = wallet.name

        # Currency
        new_currency = input(f"Currency [{wallet.currency}]: ").strip()
        if not new_currency:
            new_currency = wallet.currency

        # Description
        new_desc = input(f"Description [{wallet.description or 'N/A'}]: ").strip()
        if not new_desc:
            new_desc = wallet.description

        return {
            "new_name": new_name if new_name != wallet.name else None,
            "currency": new_currency if new_currency != wallet.currency else None,
            "description": new_desc,
        }

    @staticmethod
    def get_transfer_input(
        current_wallet: Wallet,
        available_wallets: List[Wallet]
    ) -> Optional[Dict]:
        """Get all inputs for a new transfer.

        Args:
            current_wallet: The wallet from which money is being transferred.
            available_wallets: List of all available wallets (excluding current).

        Returns:
            Dictionary with transfer details or None if cancelled.
        """
        Display.show_header("New Transfer")

        # Filter out current wallet from available options
        target_wallets = [w for w in available_wallets if w.name != current_wallet.name]

        if not target_wallets:
            Display.show_error("No other wallets available for transfer. Create another wallet first.")
            return None

        # Step 1: Select target wallet
        print(f"\nTransferring FROM: {current_wallet.name} ({current_wallet.currency})")
        print(f"Available balance: {current_wallet.balance:.2f}")
        print("\nSelect target wallet:")
        for i, wallet in enumerate(target_wallets, 1):
            print(f"   {i}. {wallet.name} ({wallet.currency}) - Balance: {wallet.balance:.2f}")

        choice = input("\nSelect wallet (number): ").strip()
        try:
            choice_num = int(choice)
            if 1 <= choice_num <= len(target_wallets):
                target_wallet = target_wallets[choice_num - 1]
            else:
                Display.show_error("Invalid selection")
                return None
        except ValueError:
            Display.show_error("Invalid selection")
            return None

        # Step 2: Amount
        amount = InputHandler.get_amount()
        if amount is None:
            return None

        # Step 3: Description
        description = InputHandler.get_description()

        # Step 4: Date
        date = InputHandler.get_datetime()

        return {
            "target_wallet_name": target_wallet.name,
            "amount": amount,
            "description": description,
            "datetime_created": date,
        }

    @staticmethod
    def get_transfer_edit_input(transfer: "Transaction") -> Optional[Dict]:
        """Get inputs for editing a transfer transaction.

        Note: For transfers, only amount, description, and date can be edited.
        The category remains 'Transfer' and wallets cannot be changed.
        """
        Display.show_header("Edit Transfer")
        Display.show_info("Press Enter to keep current value")
        Display.show_info("Note: Transfer category and wallets cannot be changed")

        print(f"\nCurrent values:")
        print(transfer.detailed_str())
        print()

        # Amount
        amount_str = input(f"Amount [{transfer.amount}]: ").strip()
        if amount_str:
            try:
                amount = float(amount_str)
                if amount <= 0:
                    Display.show_error("Amount must be positive")
                    return None
            except ValueError:
                Display.show_error("Invalid amount")
                return None
        else:
            amount = transfer.amount

        # Description
        desc_input = input(f"Description [{transfer.description or 'N/A'}]: ").strip()
        description = desc_input if desc_input else transfer.description

        # Date
        current_date = transfer.datetime_created.strftime("%Y-%m-%d")
        date_str = input(f"Date [{current_date}]: ").strip()
        if date_str:
            try:
                date = datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                Display.show_info("Invalid date format. Keeping current date.")
                date = transfer.datetime_created
        else:
            date = transfer.datetime_created

        return {
            "amount": amount,
            "description": description,
            "datetime_created": date,
        }

    # ============= Filter Input Methods =============

    @staticmethod
    def get_date_filter() -> Optional[FilterStrategy]:
        """Get a date filter from user selection."""
        Display.show_date_filter_options()
        choice = input("Select option: ").strip()

        if choice == "0":
            return None
        elif choice == "1":
            return TodayFilter()
        elif choice == "2":
            return LastWeekFilter()
        elif choice == "3":
            return LastMonthFilter()
        elif choice == "4":
            return ThisMonthFilter()
        elif choice == "5":
            return LastYearFilter()
        elif choice == "6":
            return ThisYearFilter()
        elif choice == "7":
            # Custom date range
            return InputHandler.get_custom_date_range()
        else:
            Display.show_error("Invalid option")
            return None

    @staticmethod
    def get_custom_date_range() -> Optional[FilterStrategy]:
        """Get a custom date range from user."""
        print("\nEnter date range (YYYY-MM-DD format):")
        print("Press Enter to leave a bound open")

        start_str = input("Start date (or Enter for no start): ").strip()
        end_str = input("End date (or Enter for no end): ").strip()

        start_date = None
        end_date = None

        if start_str:
            try:
                start_date = datetime.strptime(start_str, "%Y-%m-%d")
            except ValueError:
                Display.show_error("Invalid start date format")
                return None

        if end_str:
            try:
                end_date = datetime.strptime(end_str, "%Y-%m-%d").replace(
                    hour=23, minute=59, second=59
                )
            except ValueError:
                Display.show_error("Invalid end date format")
                return None

        if not start_date and not end_date:
            Display.show_info("No date range specified")
            return None

        return DateRangeFilter(start_date=start_date, end_date=end_date)

    @staticmethod
    def get_type_filter() -> Optional[FilterStrategy]:
        """Get a transaction type filter from user selection."""
        Display.show_type_filter_options()
        choice = input("Select option: ").strip()

        if choice == "0":
            return None
        elif choice == "1":
            include_transfers = InputHandler.confirm("Include incoming transfers?")
            return IncomeOnlyFilter(include_transfers=include_transfers)
        elif choice == "2":
            include_transfers = InputHandler.confirm("Include outgoing transfers?")
            return ExpenseOnlyFilter(include_transfers=include_transfers)
        elif choice == "3":
            return TransferOnlyFilter()
        elif choice == "4":
            return NoTransfersFilter()
        elif choice == "5":
            return RecurringOnlyFilter()
        elif choice == "6":
            return NonRecurringFilter()
        else:
            Display.show_error("Invalid option")
            return None

    @staticmethod
    def get_category_filter(available_categories: Set[str]) -> Optional[FilterStrategy]:
        """Get a category filter from user."""
        if not available_categories:
            Display.show_error("No categories available")
            return None

        print("\n📁 Filter Mode:")
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
            Display.show_error("Invalid option")
            return None

        # Show available categories
        sorted_categories = sorted(available_categories)
        print("\n📁 Available Categories:")
        for i, cat in enumerate(sorted_categories, 1):
            print(f"   {i}. {cat}")

        print("\nEnter category numbers separated by commas (e.g., 1,3,5):")
        selection = input("Selection: ").strip()

        if not selection:
            Display.show_info("No categories selected")
            return None

        selected_categories = set()
        try:
            indices = [int(x.strip()) for x in selection.split(",")]
            for idx in indices:
                if 1 <= idx <= len(sorted_categories):
                    selected_categories.add(sorted_categories[idx - 1])
                else:
                    Display.show_error(f"Invalid index: {idx}")
                    return None
        except ValueError:
            Display.show_error("Invalid input. Use numbers separated by commas.")
            return None

        if not selected_categories:
            Display.show_info("No valid categories selected")
            return None

        return CategoryFilter(categories=selected_categories, mode=mode)

    @staticmethod
    def get_amount_filter() -> Optional[FilterStrategy]:
        """Get an amount filter from user selection."""
        Display.show_amount_filter_options()
        choice = input("Select option: ").strip()

        if choice == "0":
            return None
        elif choice == "1":
            threshold = input("Enter minimum amount (default 10000): ").strip()
            try:
                threshold = float(threshold) if threshold else 10000
                return LargeTransactionsFilter(threshold=threshold)
            except ValueError:
                Display.show_error("Invalid amount")
                return None
        elif choice == "2":
            threshold = input("Enter maximum amount (default 100): ").strip()
            try:
                threshold = float(threshold) if threshold else 100
                return SmallTransactionsFilter(threshold=threshold)
            except ValueError:
                Display.show_error("Invalid amount")
                return None
        elif choice == "3":
            return InputHandler.get_custom_amount_range()
        else:
            Display.show_error("Invalid option")
            return None

    @staticmethod
    def get_custom_amount_range() -> Optional[FilterStrategy]:
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
                    Display.show_error("Amount cannot be negative")
                    return None
            except ValueError:
                Display.show_error("Invalid minimum amount")
                return None

        if max_str:
            try:
                max_amount = float(max_str)
                if max_amount < 0:
                    Display.show_error("Amount cannot be negative")
                    return None
            except ValueError:
                Display.show_error("Invalid maximum amount")
                return None

        if min_amount and max_amount and min_amount > max_amount:
            Display.show_error("Minimum cannot be greater than maximum")
            return None

        if min_amount is None and max_amount is None:
            Display.show_info("No amount range specified")
            return None

        return AmountRangeFilter(min_amount=min_amount, max_amount=max_amount)

    @staticmethod
    def get_description_filter() -> Optional[FilterStrategy]:
        """Get a description search filter from user."""
        search_term = input("Enter search term: ").strip()

        if not search_term:
            Display.show_info("No search term provided")
            return None

        case_sensitive = InputHandler.confirm("Case sensitive search?")
        return DescriptionFilter(search_term=search_term, case_sensitive=case_sensitive)

    @staticmethod
    def get_filter_to_remove(wallet: Wallet) -> Optional[int]:
        """Get the index of a filter to remove."""
        filters = wallet.filtering_context.active_filters
        if not filters:
            Display.show_info("No active filters to remove")
            return None

        Display.show_active_filters(wallet)
        choice = input("Enter filter number to remove (0 to cancel): ").strip()

        try:
            idx = int(choice)
            if idx == 0:
                return None
            if 1 <= idx <= len(filters):
                return idx - 1  # Convert to 0-based index
            Display.show_error("Invalid filter number")
            return None
        except ValueError:
            Display.show_error("Invalid input")
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
                Display.show_error("Interval must be at least 1. Using 1.")
                return 1
            return interval
        except ValueError:
            Display.show_info("Invalid input. Using 1.")
            return 1

    @staticmethod
    def _get_weekdays() -> Set[Weekday]:
        """Get weekday selection from user."""
        print("\nSelect days (comma-separated numbers):")
        print("   1. Monday    2. Tuesday   3. Wednesday  4. Thursday")
        print("   5. Friday    6. Saturday  7. Sunday")
        selection = input("Days: ").strip()
        if not selection:
            return set()

        weekdays = set()
        try:
            nums = [int(x.strip()) for x in selection.split(",")]
            for n in nums:
                if 1 <= n <= 7:
                    weekdays.add(Weekday(n - 1))
                else:
                    Display.show_error(f"Invalid day number: {n}")
        except ValueError:
            Display.show_error("Invalid input. Use numbers separated by commas.")
        return weekdays

    @staticmethod
    def _get_month_weekday() -> Tuple[Optional[int], Optional[Weekday]]:
        """Get 'Nth weekday of month' from user."""
        print("\nWhich occurrence? (e.g., 1st Monday)")
        week_str = input("Week number (1-5): ").strip()
        try:
            week = int(week_str)
            if not 1 <= week <= 5:
                Display.show_error("Must be between 1 and 5")
                return None, None
        except ValueError:
            Display.show_error("Invalid input")
            return None, None

        print("Which day?")
        print("   1. Monday    2. Tuesday   3. Wednesday  4. Thursday")
        print("   5. Friday    6. Saturday  7. Sunday")
        day_str = input("Day: ").strip()
        try:
            day = int(day_str)
            if 1 <= day <= 7:
                return week, Weekday(day - 1)
            Display.show_error("Invalid day number")
            return None, None
        except ValueError:
            Display.show_error("Invalid input")
            return None, None

    @staticmethod
    def _get_end_condition(rule: RecurrenceRule) -> RecurrenceRule:
        """Get end condition from user and update the rule."""
        print("\nEnd Condition:")
        print("   1. Never")
        print("   2. On a specific date")
        print("   3. After N occurrences")
        choice = input("Select (default: 1): ").strip()

        if choice == "2":
            date_str = input("End date (YYYY-MM-DD): ").strip()
            try:
                end_date = datetime.strptime(date_str, "%Y-%m-%d")
                rule.end_condition = EndCondition.ON_DATE
                rule.end_date = end_date
            except ValueError:
                Display.show_info("Invalid date. Setting to 'Never'.")
        elif choice == "3":
            count_str = input("Number of occurrences: ").strip()
            try:
                count = int(count_str)
                if count > 0:
                    rule.end_condition = EndCondition.AFTER_COUNT
                    rule.max_occurrences = count
                else:
                    Display.show_info("Must be positive. Setting to 'Never'.")
            except ValueError:
                Display.show_info("Invalid input. Setting to 'Never'.")

        return rule

    @staticmethod
    def _get_custom_recurrence() -> Optional[RecurrenceRule]:
        """Get a fully custom recurrence rule from user."""
        print("\nCustom Recurrence:")
        print("   1. Daily")
        print("   2. Weekly")
        print("   3. Monthly")
        print("   4. Yearly")
        freq_choice = input("Select frequency: ").strip()

        if freq_choice == "1":
            interval = InputHandler._get_interval("days")
            rule = RecurrenceRule(frequency=Frequency.DAILY, interval=interval)
        elif freq_choice == "2":
            interval = InputHandler._get_interval("weeks")
            weekdays = InputHandler._get_weekdays()
            rule = RecurrenceRule(
                frequency=Frequency.WEEKLY, interval=interval, weekdays=weekdays
            )
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
                rule = RecurrenceRule(
                    frequency=Frequency.MONTHLY,
                    interval=interval,
                    month_week=week,
                    month_weekday=weekday,
                )
            else:
                rule = RecurrenceRule(
                    frequency=Frequency.MONTHLY, interval=interval
                )
        elif freq_choice == "4":
            interval = InputHandler._get_interval("years")
            rule = RecurrenceRule(frequency=Frequency.YEARLY, interval=interval)
        else:
            Display.show_error("Invalid selection")
            return None

        return InputHandler._get_end_condition(rule)

    @staticmethod
    def get_recurrence_rule_input() -> Optional[RecurrenceRule]:
        """Get a recurrence rule from user via menu selection."""
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
        elif choice == "1":
            rule = RecurrenceRule(frequency=Frequency.DAILY)
        elif choice == "2":
            weekdays = InputHandler._get_weekdays()
            rule = RecurrenceRule(frequency=Frequency.WEEKLY, weekdays=weekdays)
        elif choice == "3":
            print("\nMonthly pattern:")
            print("   1. Same day of month")
            print("   2. Nth weekday (e.g., 1st Monday)")
            pattern = input("Select (default: 1): ").strip()
            if pattern == "2":
                week, weekday = InputHandler._get_month_weekday()
                if week is None:
                    return None
                rule = RecurrenceRule(
                    frequency=Frequency.MONTHLY,
                    month_week=week,
                    month_weekday=weekday,
                )
            else:
                rule = RecurrenceRule(frequency=Frequency.MONTHLY)
        elif choice == "4":
            rule = RecurrenceRule(frequency=Frequency.YEARLY)
        elif choice == "5":
            rule = RecurrenceRule(
                frequency=Frequency.WEEKLY,
                weekdays={
                    Weekday.MONDAY,
                    Weekday.TUESDAY,
                    Weekday.WEDNESDAY,
                    Weekday.THURSDAY,
                    Weekday.FRIDAY,
                },
            )
        elif choice == "6":
            return InputHandler._get_custom_recurrence()
        else:
            Display.show_error("Invalid selection")
            return None

        return InputHandler._get_end_condition(rule)

    @staticmethod
    def get_recurring_transaction_input(
        transaction_type: TransactionType,
        categories: Set[str],
        wallet_name: str,
    ) -> Optional[RecurringTransaction]:
        """Get all inputs for a new recurring transaction."""
        type_name = "Income" if transaction_type == TransactionType.INCOME else "Expense"
        Display.show_header(f"New Recurring {type_name}")

        # Step 1: Amount
        amount = InputHandler.get_amount()
        if amount is None:
            return None

        # Step 2: Category
        category = InputHandler.get_category(categories, transaction_type)
        if category is None:
            return None

        # Step 3: Description
        description = InputHandler.get_description()

        # Step 4: Start date
        print("\nStart date for recurrence:")
        start_date = InputHandler.get_datetime()

        # Step 5: Recurrence rule
        rule = InputHandler.get_recurrence_rule_input()
        if rule is None:
            return None

        return RecurringTransaction(
            amount=amount,
            transaction_type=transaction_type,
            category=category,
            description=description,
            recurrence_rule=rule,
            start_date=start_date,
            wallet_name=wallet_name,
        )

    @staticmethod
    def get_recurring_edit_input(
        recurring: RecurringTransaction, categories: Set[str]
    ) -> Optional[Dict]:
        """Get edit inputs for a recurring transaction.

        Returns a dict describing the edit action, or None if cancelled.
        """
        Display.show_header("Edit Recurring Transaction")
        print(f"\nCurrent details:")
        print(recurring.detailed_str())

        print("\nEdit Options:")
        print("   1. Edit template (affects future occurrences)")
        print("   2. Skip a specific future date")
        print("   3. Pause" if recurring.is_active else "   3. Resume")
        print("   0. Cancel")
        choice = input("Select option: ").strip()

        if choice == "0":
            return None
        elif choice == "1":
            return InputHandler._get_recurring_template_edit(recurring, categories)
        elif choice == "2":
            return InputHandler._get_recurring_skip_date()
        elif choice == "3":
            return {"action": "toggle_active"}
        else:
            Display.show_error("Invalid option")
            return None

    @staticmethod
    def _get_recurring_template_edit(
        recurring: RecurringTransaction, categories: Set[str]
    ) -> Optional[Dict]:
        """Get template field edits for a recurring transaction."""
        Display.show_info("Press Enter to keep current value")

        # Amount
        amount_str = input(f"Amount [{recurring.amount}]: ").strip()
        if amount_str:
            try:
                amount = float(amount_str)
                if amount <= 0:
                    Display.show_error("Amount must be positive")
                    return None
            except ValueError:
                Display.show_error("Invalid amount")
                return None
        else:
            amount = recurring.amount

        # Category
        print(f"\nCurrent category: {recurring.category}")
        change_cat = input("Change category? (y/n): ").strip().lower()
        if change_cat == "y":
            category = InputHandler.get_category(
                categories, recurring.transaction_type
            )
            if category is None:
                return None
        else:
            category = recurring.category

        # Description
        desc_input = input(
            f"Description [{recurring.description or 'N/A'}]: "
        ).strip()
        description = desc_input if desc_input else recurring.description

        return {
            "action": "edit_template",
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
            return {"action": "skip_date", "date": skip_date}
        except ValueError:
            Display.show_error("Invalid date format")
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
        Display.show_error("Invalid option")
        return None
