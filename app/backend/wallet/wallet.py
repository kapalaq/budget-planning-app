"""Wallet class that manages all transactions."""

import logging
import uuid
from collections import defaultdict
from datetime import datetime
from enum import Enum
from functools import singledispatchmethod
from typing import Any, Dict, List, Optional

from models.category import CategoryManager
from models.transaction import Transaction, TransactionType, Transfer
from strategies.filtering import FilteringContext
from strategies.sorting import SortingContext

logger = logging.getLogger(__name__)


DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class WalletType(Enum):
    """Enumeration for wallet types."""

    REGULAR = "regular"
    DEPOSIT = "deposit"


class GoalStatus(Enum):
    """Status of a savings goal wallet."""

    ACTIVE = "active"
    COMPLETED = "completed"
    HIDDEN = "hidden"


class Wallet:
    """Main wallet class that holds and manages all transactions."""

    wallet_type: WalletType = WalletType.REGULAR

    def __init__(
        self,
        name: str,
        starting_value: float = None,
        currency: str = "KZT",
        description: str = "",
        is_goal_wallet: bool = False,
        goal_target: Optional[float] = None,
        goal_description: Optional[str] = None,
    ):
        """
        Args:
            :param name: Name of the wallet.
            :param starting_value: A value that will present on the wallet from the beginning.
            :param currency: Currency of the wallet.
            :param description: Description of the wallet.
            :param is_goal_wallet: Whether this wallet is a savings goal.
            :param goal_target: Target amount for the savings goal.
            :param goal_description: Description of the savings goal.
        """
        # Important
        self.id = str(uuid.uuid4())[:8]
        self.name = name
        self.currency = currency
        self.__transactions: Dict[str, Transaction] = {}
        self.__category_manager = None
        self.__sorting_context = SortingContext()
        self.__filtering_context = FilteringContext()

        # Optional
        self.description = description
        self.total_expense: float = 0.0
        self.total_income: float = 0.0
        self.balance: float = 0.0
        self.datetime_created: datetime = datetime.now()

        # Goal fields
        self.is_goal_wallet: bool = is_goal_wallet
        self.goal_target: Optional[float] = goal_target
        self.goal_description: Optional[str] = goal_description
        self.goal_status: GoalStatus = GoalStatus.ACTIVE
        self.goal_created_at: Optional[datetime] = (
            datetime.now() if is_goal_wallet else None
        )
        self.goal_completed_at: Optional[datetime] = None

        if starting_value is not None:
            self.__initial_transaction = Transaction(
                amount=starting_value,
                transaction_type=TransactionType.INCOME,
                category="Перенос остатка",
            )

    @property
    def category_manager(self) -> CategoryManager:
        return self.__category_manager

    @property
    def sorting_context(self) -> SortingContext:
        return self.__sorting_context

    @property
    def filtering_context(self) -> FilteringContext:
        return self.__filtering_context

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> "Wallet":
        """Builds Wallet from persisted dict data.

        Transfer connections (source/connected) are NOT resolved here — that
        requires access to all wallets and is done in WalletManager.from_json.
        """
        if not data:
            return cls(name="Unknown")

        wallet = cls.__new__(cls)
        wallet.id = data.get("id", str(uuid.uuid4())[:8])
        wallet.name = data.get("name", "Unknown")
        wallet.currency = data.get("currency", "KZT")
        wallet.description = data.get("description", "")

        try:
            wallet.wallet_type = WalletType(data.get("wallet_type", "regular"))
        except ValueError:
            wallet.wallet_type = WalletType.REGULAR

        wallet.total_income = float(data.get("total_income", 0.0))
        wallet.total_expense = float(data.get("total_expense", 0.0))
        wallet.balance = float(data.get("balance", 0.0))
        wallet.datetime_created = datetime.strptime(
            data.get("datetime_created", datetime.now().strftime(DATETIME_FORMAT)),
            DATETIME_FORMAT,
        )

        wallet.__sorting_context = SortingContext().from_json(
            data.get("sorting_context", {})
        )
        wallet.__filtering_context = FilteringContext().from_json(
            data.get("filtering_context", {})
        )
        wallet.__category_manager = (
            CategoryManager().from_json(data.get("category_manager"))
            if data.get("category_manager")
            else None
        )

        # Goal fields
        wallet.is_goal_wallet = data.get("is_goal_wallet", False)
        wallet.goal_target = data.get("goal_target")
        wallet.goal_description = data.get("goal_description")
        try:
            wallet.goal_status = GoalStatus(data.get("goal_status", "active"))
        except ValueError:
            wallet.goal_status = GoalStatus.ACTIVE
        gc = data.get("goal_created_at")
        wallet.goal_created_at = datetime.strptime(gc, DATETIME_FORMAT) if gc else None
        gca = data.get("goal_completed_at")
        wallet.goal_completed_at = (
            datetime.strptime(gca, DATETIME_FORMAT) if gca else None
        )

        wallet.__transactions = {}
        for t_data in data.get("transactions", []):
            if t_data.get("type") == "transfer":
                t = Transfer.from_json(t_data)
            else:
                t = Transaction.from_json(t_data)
            wallet.__transactions[t.id] = t

        return wallet

    def to_json(self) -> Dict[str, Any]:
        data = {
            "id": self.id,
            "name": self.name,
            "wallet_type": self.wallet_type.value,
            "currency": self.currency,
            "description": self.description,
            "total_income": self.total_income,
            "total_expense": self.total_expense,
            "balance": self.balance,
            "datetime_created": self.datetime_created.strftime(DATETIME_FORMAT),
            "sorting_context": self.sorting_context.to_json(),
            "filtering_context": self.filtering_context.to_json(),
            "category_manager": (
                self.__category_manager.to_json() if self.__category_manager else None
            ),
            "transactions": [t.to_json() for t in self.__transactions.values()],
            "is_goal_wallet": self.is_goal_wallet,
            "goal_target": self.goal_target,
            "goal_description": self.goal_description,
            "goal_status": self.goal_status.value,
            "goal_created_at": (
                self.goal_created_at.strftime(DATETIME_FORMAT)
                if self.goal_created_at
                else None
            ),
            "goal_completed_at": (
                self.goal_completed_at.strftime(DATETIME_FORMAT)
                if self.goal_completed_at
                else None
            ),
        }
        return data

    def assign_category_manager(self, category_manager: CategoryManager):
        """Function to assign category manager."""
        self.__category_manager = category_manager
        try:
            # Check to avoid adding starting value if restoring from JSON
            if hasattr(self, "_Wallet__initial_transaction"):
                self.add_transaction(self.__initial_transaction)
                del self.__initial_transaction
        except Exception as e:
            logger.error("Category assignment failed due to {}".format(e))

    def __add_total(self, transaction: Transaction) -> None:
        """Add transactions to the total values."""
        if transaction.transaction_type == TransactionType.INCOME:
            self.total_income += transaction.amount
        elif transaction.transaction_type == TransactionType.EXPENSE:
            self.total_expense += transaction.amount
        self.balance += transaction.signed_amount

    def __del_total(self, transaction: Transaction) -> None:
        """Delete transactions from the total values."""
        if transaction.transaction_type == TransactionType.INCOME:
            self.total_income -= transaction.amount
        elif transaction.transaction_type == TransactionType.EXPENSE:
            self.total_expense -= transaction.amount
        self.balance -= transaction.signed_amount

    def add_transaction(self, transaction: Transaction) -> None:
        """Add a transaction to the wallet."""
        self.__category_manager.add_category(
            transaction.category, transaction.transaction_type
        )

        # Update 'total_' values on fly.
        self.__add_total(transaction)

        self.__transactions[transaction.id] = transaction

    @singledispatchmethod
    def get_transaction(self, index) -> Optional[Transaction]:
        """Get a transaction by its display index (1-based)."""
        sorted_transactions = self.get_sorted_transactions()
        if 1 <= index <= len(sorted_transactions):
            return sorted_transactions[index - 1]
        return None

    @get_transaction.register
    def _(self, index: str) -> Optional[Transaction]:
        """Get a transaction by its ID."""
        return self.__transactions.get(index, None)

    def update_transaction(
        self, index: Optional[int | str], updated: Transaction
    ) -> bool:
        """Update a transaction by its display index or ID."""
        old_transaction = self.get_transaction(index)

        if old_transaction is not None:
            self.__del_total(old_transaction)

            # If it's a transfer, we need to update the connected wallet's totals too
            if isinstance(old_transaction, Transfer) and old_transaction.connected:
                connected = old_transaction.connected
                if connected.source:
                    connected.source._Wallet__del_total(connected)

            # Update the transaction (Transfer.update will sync with connected)
            result = old_transaction.update(updated)

            # Add back the totals
            self.__add_total(old_transaction)

            # If it's a transfer, update the connected wallet's totals
            if isinstance(old_transaction, Transfer) and old_transaction.connected:
                connected = old_transaction.connected
                if connected.source:
                    connected.source._Wallet__add_total(connected)

            return result
        return False

    def delete_transaction(
        self, index: Optional[int | str], delete_connected: bool = True
    ) -> bool:
        """Delete a transaction by its display index or ID."""
        transaction_to_delete = self.get_transaction(index)
        if transaction_to_delete is not None:
            self.__del_total(transaction_to_delete)
            self.__transactions.pop(transaction_to_delete.id, None)

            # Handle transfer deletion - delete connected transaction too
            if delete_connected and isinstance(transaction_to_delete, Transfer):
                connected = transaction_to_delete.connected
                if connected is not None and connected.source is not None:
                    # Clear the connection to prevent infinite recursion
                    transaction_to_delete.connected = None
                    connected.connected = None
                    # Delete the connected transaction from the other wallet
                    connected.source.delete_transaction(
                        connected.id, delete_connected=False
                    )
            return True
        return False

    def get_sorted_transactions(self) -> List[Transaction]:
        """Get all transactions sorted by current strategy."""
        return self.__sorting_context.sort(self.__transactions.values())

    def get_filtered_transactions(self) -> List[Transaction]:
        """Get transactions filtered and sorted by current strategies."""
        transactions = list(self.__transactions.values())
        filtered = self.__filtering_context.filter(transactions)
        return self.__sorting_context.sort(filtered)

    def get_category_totals(self) -> Dict[str, float]:
        """Get total amount per category (only non-zero)."""
        totals: Dict[str, float] = defaultdict(float)
        for t in self.__transactions.values():
            totals[t.category] += t.signed_amount
        return {k: v for k, v in totals.items() if v != 0}

    def get_income_by_category(self) -> Dict[str, float]:
        """Get income totals grouped by category."""
        totals: Dict[str, float] = defaultdict(float)
        for t in self.__transactions.values():
            if t.transaction_type == TransactionType.INCOME:
                totals[t.category] += t.amount
        return {k: v for k, v in totals.items() if v != 0}

    def get_expense_by_category(self) -> Dict[str, float]:
        """Get expense totals grouped by category."""
        totals: Dict[str, float] = defaultdict(float)
        for t in self.__transactions.values():
            if t.transaction_type == TransactionType.EXPENSE:
                totals[t.category] += t.amount
        return {k: v for k, v in totals.items() if v != 0}

    def get_income_percentages(self) -> Dict[str, float]:
        """Get percentage of each income category relative to total income."""
        if self.total_income == 0:
            return {}
        income_by_cat = self.get_income_by_category()
        return {
            category: (amount / self.total_income) * 100
            for category, amount in income_by_cat.items()
        }

    def get_expense_percentages(self) -> Dict[str, float]:
        """Get percentage of each expense category relative to total expense."""
        if self.total_expense == 0:
            return {}
        expense_by_cat = self.get_expense_by_category()
        return {
            category: (amount / self.total_expense) * 100
            for category, amount in expense_by_cat.items()
        }

    def get_category_percentages(self) -> Dict[str, float]:
        """Get percentage contribution of each category to total absolute value."""
        total_absolute = self.total_expense
        if total_absolute == 0:
            return {}

        category_absolutes = self.get_category_totals()

        return {
            category: (abs(amount) / total_absolute) * 100
            for category, amount in category_absolutes.items()
            if amount != 0
        }

    def get_transactions_by_recurrence(self, recurrence_id: str) -> List[Transaction]:
        """Get all transactions generated by a specific recurring transaction."""
        return [
            t
            for t in self.__transactions.values()
            if getattr(t, "recurrence_id", None) == recurrence_id
        ]

    def delete_future_by_recurrence(self, recurrence_id: str) -> int:
        """Delete future transactions generated by a recurring transaction."""
        now = datetime.now()
        to_delete = [
            t
            for t in self.__transactions.values()
            if getattr(t, "recurrence_id", None) == recurrence_id
            and t.datetime_created > now
        ]
        for t in to_delete:
            self.delete_transaction(t.id)
        return len(to_delete)

    def transaction_count(self) -> int:
        """Return the number of transactions."""
        return len(self.__transactions)

    def delete(self):
        """Pre-Destructor of a wallet."""
        transactions = list(self.__transactions.values())
        for transaction in transactions:
            self.delete_transaction(transaction.id)

    def __del__(self):
        """Destructor of a wallet."""
        self.delete()


class DepositWallet(Wallet):
    """Deposit wallet with interest rate and maturity date."""

    wallet_type: WalletType = WalletType.DEPOSIT

    def __init__(
        self,
        name: str,
        interest_rate: float,
        term_months: int,
        starting_value: float = None,
        currency: str = "KZT",
        description: str = "",
        capitalization: bool = False,
    ):
        super().__init__(name, starting_value, currency, description)
        self.interest_rate = interest_rate
        self.term_months = term_months
        self.capitalization = capitalization
        self.maturity_date = self._calculate_maturity_date()

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> "DepositWallet":
        """Builds DepositWallet from persisted dict data."""
        if not data:
            return cls(name="Unknown", interest_rate=0.0, term_months=0)

        # Use Wallet.from_json but change the class tag so __del__ doesn't
        # destroy shared state when the temporary goes out of scope.
        # We override wallet_type on the data so Wallet.from_json uses our cls.
        deposit = Wallet.from_json.__func__(cls, data)
        deposit.wallet_type = WalletType.DEPOSIT

        deposit.interest_rate = float(data.get("interest_rate", 0.0))
        deposit.term_months = int(data.get("term_months", 0))
        deposit.capitalization = bool(data.get("capitalization", False))

        m_date = data.get("maturity_date")
        if m_date:
            deposit.maturity_date = datetime.strptime(m_date, DATETIME_FORMAT)
        else:
            deposit.maturity_date = deposit._calculate_maturity_date()

        return deposit

    def to_json(self) -> Dict[str, Any]:
        """Turns DepositWallet data into dict, including base Wallet attributes."""
        data = super().to_json()
        data.update(
            {
                "interest_rate": self.interest_rate,
                "term_months": self.term_months,
                "capitalization": self.capitalization,
                "maturity_date": self.maturity_date.strftime(DATETIME_FORMAT),
            }
        )
        return data

    def _calculate_maturity_date(self) -> datetime:
        """Calculate the maturity date based on term."""
        year = self.datetime_created.year
        month = self.datetime_created.month + self.term_months

        # Handle year overflow
        while month > 12:
            month -= 12
            year += 1

        # Handle day overflow (e.g., Jan 31 + 1 month)
        day = min(self.datetime_created.day, self._days_in_month(year, month))

        return datetime(
            year,
            month,
            day,
            self.datetime_created.hour,
            self.datetime_created.minute,
            self.datetime_created.second,
        )

    @staticmethod
    def _days_in_month(year: int, month: int) -> int:
        """Get the number of days in a given month."""
        if month in (1, 3, 5, 7, 8, 10, 12):
            return 31
        elif month in (4, 6, 9, 11):
            return 30
        elif month == 2:
            # Leap year check
            if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
                return 29
            return 28
        return 30

    @property
    def principal(self) -> float:
        """Get the initial deposit amount (first income transaction)."""
        return self.total_income

    @property
    def monthly_rate(self) -> float:
        """Get the monthly interest rate."""
        return self.interest_rate / 12 / 100

    @property
    def is_matured(self) -> bool:
        """Check if the deposit has reached maturity."""
        return datetime.now() >= self.maturity_date

    @property
    def days_until_maturity(self) -> int:
        """Get the number of days until maturity."""
        if self.is_matured:
            return 0
        delta = self.maturity_date - datetime.now()
        return delta.days

    @property
    def months_elapsed(self) -> int:
        """Get the number of complete months since deposit creation."""
        now = datetime.now()
        if now > self.maturity_date:
            now = self.maturity_date

        years_diff = now.year - self.datetime_created.year
        months_diff = now.month - self.datetime_created.month

        total_months = years_diff * 12 + months_diff

        # Adjust if we haven't reached the same day in the month
        if now.day < self.datetime_created.day:
            total_months -= 1

        return max(0, total_months)

    def calculate_accrued_interest(self) -> float:
        """Calculate the interest accrued so far."""
        months = self.months_elapsed
        principal = self.principal

        if self.capitalization:
            # Compound interest: P * (1 + r)^n - P
            return principal * ((1 + self.monthly_rate) ** months) - principal
        else:
            # Simple interest: P * r * n
            return principal * self.monthly_rate * months

    def calculate_total_interest(self) -> float:
        """Calculate the total interest at maturity."""
        if self.capitalization:
            # Compound interest
            return (
                self.principal * ((1 + self.monthly_rate) ** self.term_months)
                - self.principal
            )
        else:
            # Simple interest
            return self.principal * self.monthly_rate * self.term_months

    def calculate_maturity_amount(self) -> float:
        """Calculate the total amount at maturity (principal + interest)."""
        return self.principal + self.calculate_total_interest()

    def get_deposit_summary(self) -> Dict:
        """Get a summary of the deposit details."""
        return {
            "principal": self.principal,
            "interest_rate": self.interest_rate,
            "term_months": self.term_months,
            "capitalization": self.capitalization,
            "maturity_date": self.maturity_date,
            "is_matured": self.is_matured,
            "days_until_maturity": self.days_until_maturity,
            "accrued_interest": self.calculate_accrued_interest(),
            "total_interest": self.calculate_total_interest(),
            "maturity_amount": self.calculate_maturity_amount(),
        }
