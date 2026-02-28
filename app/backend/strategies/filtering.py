"""Filtering strategies for transactions using Strategy Pattern."""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, List, Optional, Set

from models.transaction import Transaction, TransactionType, Transfer

if TYPE_CHECKING:
    pass


class FilterStrategy(ABC):
    """Abstract base class for filtering strategies."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of the filter."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Return a description of the current filter state."""
        pass

    @abstractmethod
    def matches(self, transaction: Transaction) -> bool:
        """Return True if the transaction matches the filter criteria."""
        pass

    def filter(self, transactions: List[Transaction]) -> List[Transaction]:
        """Filter transactions according to the strategy."""
        return [t for t in transactions if self.matches(t)]


# ============= Date Range Filters =============


class DateRangeFilter(FilterStrategy):
    """Filter transactions by date range."""

    def __init__(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ):
        self._start_date = start_date
        self._end_date = end_date

    @property
    def name(self) -> str:
        return "Date Range"

    @property
    def start_date(self) -> Optional[datetime]:
        return self._start_date

    @property
    def end_date(self) -> Optional[datetime]:
        return self._end_date

    @property
    def description(self) -> str:
        if self._start_date and self._end_date:
            return (
                f"{self._start_date.strftime('%Y-%m-%d')} to "
                f"{self._end_date.strftime('%Y-%m-%d')}"
            )
        elif self._start_date:
            return f"From {self._start_date.strftime('%Y-%m-%d')}"
        elif self._end_date:
            return f"Until {self._end_date.strftime('%Y-%m-%d')}"
        return "All dates"

    def matches(self, transaction: Transaction) -> bool:
        t_date = transaction.datetime_created
        if self._start_date and t_date < self._start_date:
            return False
        if self._end_date and t_date > self._end_date:
            return False
        return True


class TodayFilter(DateRangeFilter):
    """Filter transactions from today only."""

    def __init__(self):
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)
        super().__init__(start_date=today, end_date=tomorrow)

    @property
    def name(self) -> str:
        return "Today"

    @property
    def description(self) -> str:
        return "Today"


class LastWeekFilter(DateRangeFilter):
    """Filter transactions from the last 7 days."""

    def __init__(self):
        now = datetime.now()
        week_ago = (now - timedelta(days=7)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        super().__init__(start_date=week_ago, end_date=now)

    @property
    def name(self) -> str:
        return "Last Week"

    @property
    def description(self) -> str:
        return "Last 7 days"


class LastMonthFilter(DateRangeFilter):
    """Filter transactions from the last 30 days."""

    def __init__(self):
        now = datetime.now()
        month_ago = (now - timedelta(days=30)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        super().__init__(start_date=month_ago, end_date=now)

    @property
    def name(self) -> str:
        return "Last Month"

    @property
    def description(self) -> str:
        return "Last 30 days"


class LastYearFilter(DateRangeFilter):
    """Filter transactions from the last 365 days."""

    def __init__(self):
        now = datetime.now()
        year_ago = (now - timedelta(days=365)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        super().__init__(start_date=year_ago, end_date=now)

    @property
    def name(self) -> str:
        return "Last Year"

    @property
    def description(self) -> str:
        return "Last 365 days"


class ThisMonthFilter(DateRangeFilter):
    """Filter transactions from the current calendar month."""

    def __init__(self):
        now = datetime.now()
        first_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        super().__init__(start_date=first_of_month, end_date=now)

    @property
    def name(self) -> str:
        return "This Month"

    @property
    def description(self) -> str:
        return f"This month ({datetime.now().strftime('%B %Y')})"


class ThisYearFilter(DateRangeFilter):
    """Filter transactions from the current calendar year."""

    def __init__(self):
        now = datetime.now()
        first_of_year = now.replace(
            month=1, day=1, hour=0, minute=0, second=0, microsecond=0
        )
        super().__init__(start_date=first_of_year, end_date=now)

    @property
    def name(self) -> str:
        return "This Year"

    @property
    def description(self) -> str:
        return f"This year ({datetime.now().year})"


# ============= Category Filters =============


class CategoryFilter(FilterStrategy):
    """Filter transactions by category (include or exclude mode)."""

    def __init__(
        self,
        categories: Set[str],
        mode: str = "include",
    ):
        """
        Args:
            categories: Set of category names to filter by.
            mode: 'include' to show only these categories,
                  'exclude' to hide these categories.
        """
        self._categories = {c.lower() for c in categories}
        self._original_categories = categories
        self._mode = mode.lower()

    @property
    def name(self) -> str:
        return "Category"

    @property
    def description(self) -> str:
        cats = ", ".join(sorted(self._original_categories))
        if self._mode == "include":
            return f"Only: {cats}"
        return f"Excluding: {cats}"

    def matches(self, transaction: Transaction) -> bool:
        cat_lower = transaction.category.lower()
        if self._mode == "include":
            return cat_lower in self._categories
        return cat_lower not in self._categories


# ============= Transaction Type Filters =============


class TransactionTypeFilter(FilterStrategy):
    """Filter transactions by type (income, expense, or transfer)."""

    def __init__(
        self, transaction_type: TransactionType, include_transfers: bool = True
    ):
        """
        Args:
            transaction_type: The type to filter for (INCOME or EXPENSE).
            include_transfers: Whether to include transfer transactions of this type.
        """
        self._type = transaction_type
        self._include_transfers = include_transfers

    @property
    def name(self) -> str:
        return "Transaction Type"

    @property
    def description(self) -> str:
        type_name = "Income" if self._type == TransactionType.INCOME else "Expense"
        if self._include_transfers:
            return f"{type_name} (including transfers)"
        return f"{type_name} only"

    def matches(self, transaction: Transaction) -> bool:
        if not self._include_transfers and isinstance(transaction, Transfer):
            return False
        return transaction.transaction_type == self._type


class IncomeOnlyFilter(TransactionTypeFilter):
    """Filter to show only income transactions."""

    def __init__(self, include_transfers: bool = True):
        super().__init__(TransactionType.INCOME, include_transfers)

    @property
    def name(self) -> str:
        return "Income Only"

    @property
    def description(self) -> str:
        if self._include_transfers:
            return "Income transactions"
        return "Income (no transfers)"


class ExpenseOnlyFilter(TransactionTypeFilter):
    """Filter to show only expense transactions."""

    def __init__(self, include_transfers: bool = True):
        super().__init__(TransactionType.EXPENSE, include_transfers)

    @property
    def name(self) -> str:
        return "Expense Only"

    @property
    def description(self) -> str:
        if self._include_transfers:
            return "Expense transactions"
        return "Expense (no transfers)"


class TransferOnlyFilter(FilterStrategy):
    """Filter to show only transfer transactions."""

    @property
    def name(self) -> str:
        return "Transfers Only"

    @property
    def description(self) -> str:
        return "Transfer transactions"

    def matches(self, transaction: Transaction) -> bool:
        return isinstance(transaction, Transfer)


class NoTransfersFilter(FilterStrategy):
    """Filter to exclude transfer transactions."""

    @property
    def name(self) -> str:
        return "No Transfers"

    @property
    def description(self) -> str:
        return "Excluding transfers"

    def matches(self, transaction: Transaction) -> bool:
        return not isinstance(transaction, Transfer)


class RecurringOnlyFilter(FilterStrategy):
    """Filter to show only recurring transactions."""

    @property
    def name(self) -> str:
        return "Recurring Only"

    @property
    def description(self) -> str:
        return "Recurring transactions"

    def matches(self, transaction: Transaction) -> bool:
        return getattr(transaction, "recurrence_id", None) is not None


class NonRecurringFilter(FilterStrategy):
    """Filter to show only non-recurring transactions."""

    @property
    def name(self) -> str:
        return "Non-Recurring Only"

    @property
    def description(self) -> str:
        return "Non-recurring transactions"

    def matches(self, transaction: Transaction) -> bool:
        return getattr(transaction, "recurrence_id", None) is None


# ============= Amount Range Filters =============


class AmountRangeFilter(FilterStrategy):
    """Filter transactions by amount range."""

    def __init__(
        self,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
    ):
        """
        Args:
            min_amount: Minimum amount (inclusive). Uses absolute value.
            max_amount: Maximum amount (inclusive). Uses absolute value.
        """
        self._min_amount = min_amount
        self._max_amount = max_amount

    @property
    def name(self) -> str:
        return "Amount Range"

    @property
    def description(self) -> str:
        if self._min_amount is not None and self._max_amount is not None:
            return f"{self._min_amount:.2f} - {self._max_amount:.2f}"
        elif self._min_amount is not None:
            return f">= {self._min_amount:.2f}"
        elif self._max_amount is not None:
            return f"<= {self._max_amount:.2f}"
        return "Any amount"

    def matches(self, transaction: Transaction) -> bool:
        amount = abs(transaction.amount)
        if self._min_amount is not None and amount < self._min_amount:
            return False
        if self._max_amount is not None and amount > self._max_amount:
            return False
        return True


class LargeTransactionsFilter(AmountRangeFilter):
    """Filter for transactions above a threshold (default 10000)."""

    def __init__(self, threshold: float = 10000):
        super().__init__(min_amount=threshold)
        self._threshold = threshold

    @property
    def name(self) -> str:
        return "Large Transactions"

    @property
    def description(self) -> str:
        return f"Amount >= {self._threshold:.2f}"


class SmallTransactionsFilter(AmountRangeFilter):
    """Filter for transactions below a threshold (default 100)."""

    def __init__(self, threshold: float = 100):
        super().__init__(max_amount=threshold)
        self._threshold = threshold

    @property
    def name(self) -> str:
        return "Small Transactions"

    @property
    def description(self) -> str:
        return f"Amount <= {self._threshold:.2f}"


# ============= Description Filter =============


class DescriptionFilter(FilterStrategy):
    """Filter transactions by description substring search."""

    def __init__(self, search_term: str, case_sensitive: bool = False):
        self._search_term = search_term
        self._case_sensitive = case_sensitive
        self._search_lower = search_term.lower()

    @property
    def name(self) -> str:
        return "Description"

    @property
    def description(self) -> str:
        return f'Contains "{self._search_term}"'

    def matches(self, transaction: Transaction) -> bool:
        desc = transaction.description
        if not desc:
            return False
        if self._case_sensitive:
            return self._search_term in desc
        return self._search_lower in desc.lower()


# ============= Composite Filter =============


class CompositeFilter(FilterStrategy):
    """Combines multiple filters with AND logic."""

    def __init__(self, filters: Optional[List[FilterStrategy]] = None):
        self._filters: List[FilterStrategy] = filters or []

    @property
    def name(self) -> str:
        return "Combined Filters"

    @property
    def description(self) -> str:
        if not self._filters:
            return "No filters applied"
        return " + ".join(f.name for f in self._filters)

    @property
    def filters(self) -> List[FilterStrategy]:
        return self._filters.copy()

    @property
    def filter_count(self) -> int:
        return len(self._filters)

    def add_filter(self, filter_strategy: FilterStrategy) -> None:
        """Add a filter to the composite."""
        self._filters.append(filter_strategy)

    def remove_filter(self, index: int) -> bool:
        """Remove a filter by index."""
        if 0 <= index < len(self._filters):
            self._filters.pop(index)
            return True
        return False

    def clear_filters(self) -> None:
        """Remove all filters."""
        self._filters.clear()

    def matches(self, transaction: Transaction) -> bool:
        """Returns True only if all filters match (AND logic)."""
        return all(f.matches(transaction) for f in self._filters)

    def filter(self, transactions: List[Transaction]) -> List[Transaction]:
        """Apply all filters sequentially."""
        if not self._filters:
            return transactions
        result = transactions
        for f in self._filters:
            result = f.filter(result)
        return result


# ============= Filtering Context =============


class FilteringContext:
    """Context class that manages filtering strategies."""

    # Predefined filter presets
    DATE_PRESETS = {
        "1": ("Today", TodayFilter),
        "2": ("Last Week", LastWeekFilter),
        "3": ("Last Month", LastMonthFilter),
        "4": ("This Month", ThisMonthFilter),
        "5": ("Last Year", LastYearFilter),
        "6": ("This Year", ThisYearFilter),
        "7": ("Custom Date Range", DateRangeFilter),
    }

    TYPE_PRESETS = {
        "1": ("Income Only", IncomeOnlyFilter),
        "2": ("Expense Only", ExpenseOnlyFilter),
        "3": ("Transfers Only", TransferOnlyFilter),
        "4": ("No Transfers", NoTransfersFilter),
        "5": ("Recurring Only", RecurringOnlyFilter),
        "6": ("Non-Recurring Only", NonRecurringFilter),
    }

    AMOUNT_PRESETS = {
        "1": ("Large Transactions (>= 10000)", lambda: LargeTransactionsFilter(10000)),
        "2": ("Small Transactions (<= 100)", lambda: SmallTransactionsFilter(100)),
        "3": ("Custom Amount Range", AmountRangeFilter),
    }

    def __init__(self):
        self._composite = CompositeFilter()

    @property
    def active_filters(self) -> List[FilterStrategy]:
        """Return list of active filters."""
        return self._composite.filters

    @property
    def has_filters(self) -> bool:
        """Return True if any filters are active."""
        return self._composite.filter_count > 0

    @property
    def filter_summary(self) -> str:
        """Return a summary of active filters."""
        if not self.has_filters:
            return "None"
        descriptions = [f"{f.name}: {f.description}" for f in self._composite.filters]
        return ", ".join(descriptions)

    def add_filter(self, filter_strategy: FilterStrategy) -> None:
        """Add a new filter."""
        self._composite.add_filter(filter_strategy)

    def remove_filter(self, index: int) -> bool:
        """Remove a filter by index (0-based)."""
        return self._composite.remove_filter(index)

    def clear_filters(self) -> None:
        """Remove all filters."""
        self._composite.clear_filters()

    def filter(self, transactions: List[Transaction]) -> List[Transaction]:
        """Apply all active filters to transactions."""
        return self._composite.filter(transactions)

    @classmethod
    def get_date_presets(cls) -> dict:
        """Return available date filter presets."""
        return {key: name for key, (name, _) in cls.DATE_PRESETS.items()}

    @classmethod
    def get_type_presets(cls) -> dict:
        """Return available type filter presets."""
        return {key: name for key, (name, _) in cls.TYPE_PRESETS.items()}

    @classmethod
    def get_amount_presets(cls) -> dict:
        """Return available amount filter presets."""
        return {key: name for key, (name, _) in cls.AMOUNT_PRESETS.items()}
