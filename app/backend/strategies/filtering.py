from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set

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

    @abstractmethod
    def to_json(self) -> Dict[str, Any]:
        """Serialize the filter configuration into a dictionary."""
        pass

    @abstractmethod
    def from_json(self, data: Dict[str, Any]) -> "FilterStrategy":
        """Load the filter configuration from a dictionary."""
        pass


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

    def to_json(self) -> Dict[str, Any]:
        return {
            "type": self.__class__.__name__,
            "start_date": self._start_date.isoformat() if self._start_date else None,
            "end_date": self._end_date.isoformat() if self._end_date else None,
        }

    def from_json(self, data: Dict[str, Any]) -> "DateRangeFilter":
        s_date = data.get("start_date")
        e_date = data.get("end_date")
        self._start_date = datetime.fromisoformat(s_date) if s_date else None
        self._end_date = datetime.fromisoformat(e_date) if e_date else None
        return self


class TodayFilter(DateRangeFilter):
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
    def __init__(self):
        week_ago = (datetime.now() - timedelta(days=7)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        super().__init__(start_date=week_ago)

    @property
    def name(self) -> str:
        return "Last Week"

    @property
    def description(self) -> str:
        return "Last 7 days"


class LastMonthFilter(DateRangeFilter):
    def __init__(self):
        month_ago = (datetime.now() - timedelta(days=30)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        super().__init__(start_date=month_ago)

    @property
    def name(self) -> str:
        return "Last Month"

    @property
    def description(self) -> str:
        return "Last 30 days"


class LastYearFilter(DateRangeFilter):
    def __init__(self):
        year_ago = (datetime.now() - timedelta(days=365)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        super().__init__(start_date=year_ago)

    @property
    def name(self) -> str:
        return "Last Year"

    @property
    def description(self) -> str:
        return "Last 365 days"


class ThisMonthFilter(DateRangeFilter):
    def __init__(self):
        first_of_month = datetime.now().replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        super().__init__(start_date=first_of_month)

    @property
    def name(self) -> str:
        return "This Month"

    @property
    def description(self) -> str:
        return f"This month ({datetime.now().strftime('%B %Y')})"


class ThisYearFilter(DateRangeFilter):
    def __init__(self):
        first_of_year = datetime.now().replace(
            month=1, day=1, hour=0, minute=0, second=0, microsecond=0
        )
        super().__init__(start_date=first_of_year)

    @property
    def name(self) -> str:
        return "This Year"

    @property
    def description(self) -> str:
        return f"This year ({datetime.now().year})"


# ============= Category Filters =============


class CategoryFilter(FilterStrategy):
    def __init__(
        self,
        categories: Set[str],
        mode: str = "include",
    ):
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

    def to_json(self) -> Dict[str, Any]:
        return {
            "type": self.__class__.__name__,
            "categories": list(self._original_categories),
            "mode": self._mode,
        }

    def from_json(self, data: Dict[str, Any]) -> "CategoryFilter":
        self._original_categories = set(data.get("categories", []))
        self._categories = {c.lower() for c in self._original_categories}
        self._mode = data.get("mode", "include").lower()
        return self


# ============= Transaction Type Filters =============


class TransactionTypeFilter(FilterStrategy):
    def __init__(
        self, transaction_type: TransactionType, include_transfers: bool = True
    ):
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

    def to_json(self) -> Dict[str, Any]:
        return {
            "type": self.__class__.__name__,
            "transaction_type": self._type.value,
            "include_transfers": self._include_transfers,
        }

    def from_json(self, data: Dict[str, Any]) -> "TransactionTypeFilter":
        type_str = data.get("transaction_type")
        try:
            self._type = TransactionType(type_str)
        except (KeyError, TypeError):
            pass
        self._include_transfers = data.get("include_transfers", True)
        return self


class IncomeOnlyFilter(TransactionTypeFilter):
    def __init__(self, include_transfers: bool = True):
        super().__init__(TransactionType.INCOME, include_transfers)

    @property
    def name(self) -> str:
        return "Income Only"

    @property
    def description(self) -> str:
        return (
            "Income transactions"
            if self._include_transfers
            else "Income (no transfers)"
        )


class ExpenseOnlyFilter(TransactionTypeFilter):
    def __init__(self, include_transfers: bool = True):
        super().__init__(TransactionType.EXPENSE, include_transfers)

    @property
    def name(self) -> str:
        return "Expense Only"

    @property
    def description(self) -> str:
        return (
            "Expense transactions"
            if self._include_transfers
            else "Expense (no transfers)"
        )


class TransferOnlyFilter(FilterStrategy):
    @property
    def name(self) -> str:
        return "Transfers Only"

    @property
    def description(self) -> str:
        return "Transfer transactions"

    def matches(self, transaction: Transaction) -> bool:
        return isinstance(transaction, Transfer)

    def to_json(self) -> Dict[str, Any]:
        return {"type": self.__class__.__name__}

    def from_json(self, data: Dict[str, Any]) -> "TransferOnlyFilter":
        return self


class NoTransfersFilter(FilterStrategy):
    @property
    def name(self) -> str:
        return "No Transfers"

    @property
    def description(self) -> str:
        return "Excluding transfers"

    def matches(self, transaction: Transaction) -> bool:
        return not isinstance(transaction, Transfer)

    def to_json(self) -> Dict[str, Any]:
        return {"type": self.__class__.__name__}

    def from_json(self, data: Dict[str, Any]) -> "NoTransfersFilter":
        return self


class RecurringOnlyFilter(FilterStrategy):
    @property
    def name(self) -> str:
        return "Recurring Only"

    @property
    def description(self) -> str:
        return "Recurring transactions"

    def matches(self, transaction: Transaction) -> bool:
        return getattr(transaction, "recurrence_id", None) is not None

    def to_json(self) -> Dict[str, Any]:
        return {"type": self.__class__.__name__}

    def from_json(self, data: Dict[str, Any]) -> "RecurringOnlyFilter":
        return self


class NonRecurringFilter(FilterStrategy):
    @property
    def name(self) -> str:
        return "Non-Recurring Only"

    @property
    def description(self) -> str:
        return "Non-recurring transactions"

    def matches(self, transaction: Transaction) -> bool:
        return getattr(transaction, "recurrence_id", None) is None

    def to_json(self) -> Dict[str, Any]:
        return {"type": self.__class__.__name__}

    def from_json(self, data: Dict[str, Any]) -> "NonRecurringFilter":
        return self


# ============= Amount Range Filters =============


class AmountRangeFilter(FilterStrategy):
    def __init__(
        self,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
    ):
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

    def to_json(self) -> Dict[str, Any]:
        return {
            "type": self.__class__.__name__,
            "min_amount": self._min_amount,
            "max_amount": self._max_amount,
        }

    def from_json(self, data: Dict[str, Any]) -> "AmountRangeFilter":
        self._min_amount = data.get("min_amount")
        self._max_amount = data.get("max_amount")
        return self


class LargeTransactionsFilter(AmountRangeFilter):
    def __init__(self, threshold: float = 10000):
        super().__init__(min_amount=threshold)
        self._threshold = threshold

    @property
    def name(self) -> str:
        return "Large Transactions"

    @property
    def description(self) -> str:
        return f"Amount >= {self._threshold:.2f}"

    def to_json(self) -> Dict[str, Any]:
        data = super().to_json()
        data["threshold"] = self._threshold
        return data

    def from_json(self, data: Dict[str, Any]) -> "LargeTransactionsFilter":
        super().from_json(data)
        self._threshold = data.get("threshold", 10000)
        return self


class SmallTransactionsFilter(AmountRangeFilter):
    def __init__(self, threshold: float = 100):
        super().__init__(max_amount=threshold)
        self._threshold = threshold

    @property
    def name(self) -> str:
        return "Small Transactions"

    @property
    def description(self) -> str:
        return f"Amount <= {self._threshold:.2f}"

    def to_json(self) -> Dict[str, Any]:
        data = super().to_json()
        data["threshold"] = self._threshold
        return data

    def from_json(self, data: Dict[str, Any]) -> "SmallTransactionsFilter":
        super().from_json(data)
        self._threshold = data.get("threshold", 100)
        return self


# ============= Description Filter =============


class DescriptionFilter(FilterStrategy):
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

    def to_json(self) -> Dict[str, Any]:
        return {
            "type": self.__class__.__name__,
            "search_term": self._search_term,
            "case_sensitive": self._case_sensitive,
        }

    def from_json(self, data: Dict[str, Any]) -> "DescriptionFilter":
        self._search_term = data.get("search_term", "")
        self._case_sensitive = data.get("case_sensitive", False)
        self._search_lower = self._search_term.lower()
        return self


# ============= Composite Filter =============


class CompositeFilter(FilterStrategy):
    def __init__(self, filters: Optional[List[FilterStrategy]] = None):
        self._filters: List[FilterStrategy] = filters or []

    @property
    def name(self) -> str:
        return "Combined Filters"

    @property
    def description(self) -> str:
        if not self._filters:
            return "No filters applied"
        return " + ".join(set(f.name for f in self._filters))

    @property
    def filters(self) -> List[FilterStrategy]:
        return self._filters.copy()

    @property
    def filter_count(self) -> int:
        return len(self._filters)

    def add_filter(self, filter_strategy: FilterStrategy) -> None:
        self._filters.append(filter_strategy)

    def remove_filter(self, index: int) -> bool:
        if 0 <= index < len(self._filters):
            self._filters.pop(index)
            return True
        return False

    def clear_filters(self) -> None:
        self._filters.clear()

    def matches(self, transaction: Transaction) -> bool:
        return all(f.matches(transaction) for f in self._filters)

    def filter(self, transactions: List[Transaction]) -> List[Transaction]:
        if not self._filters:
            return transactions
        result = transactions
        for f in self._filters:
            result = f.filter(result)
        return result

    def to_json(self) -> Dict[str, Any]:
        return {
            "type": self.__class__.__name__,
            "filters": [f.to_json() for f in self._filters],
        }

    def from_json(self, data: Dict[str, Any]) -> "CompositeFilter":
        self.clear_filters()
        for f_data in data.get("filters", []):
            cls_name = f_data.get("type")
            # Using globals() to dynamically instantiate classes based on their name.
            if cls_name in globals():
                cls = globals()[cls_name]
                # Bypassing __init__ using __new__ so we can hydrate the state securely via from_json
                obj = cls.__new__(cls)
                obj.from_json(f_data)
                self.add_filter(obj)
        return self


# ============= Filtering Context =============


class FilteringContext:
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
        return self._composite.filters

    @property
    def has_filters(self) -> bool:
        return self._composite.filter_count > 0

    @property
    def filter_summary(self) -> str:
        if not self.has_filters:
            return "None"
        descriptions = [f"{f.name}: {f.description}" for f in self._composite.filters]
        return ", ".join(descriptions)

    def add_filter(self, filter_strategy: FilterStrategy) -> None:
        self._composite.add_filter(filter_strategy)

    def remove_filter(self, index: int) -> bool:
        return self._composite.remove_filter(index)

    def clear_filters(self) -> None:
        self._composite.clear_filters()

    def filter(self, transactions: List[Transaction]) -> List[Transaction]:
        return self._composite.filter(transactions)

    def to_json(self) -> Dict[str, Any]:
        """Turns FilteringContext data into dict for persistance."""
        return {"composite": self._composite.to_json()}

    def from_json(self, data: Dict[str, Any]) -> "FilteringContext":
        """Builds FilteringContext class from persisted dict data."""
        if not data:
            return self

        comp_data = data.get("composite", {})
        if comp_data:
            self._composite.from_json(comp_data)

        return self

    @classmethod
    def get_date_presets(cls) -> dict:
        return {key: name for key, (name, _) in cls.DATE_PRESETS.items()}

    @classmethod
    def get_type_presets(cls) -> dict:
        return {key: name for key, (name, _) in cls.TYPE_PRESETS.items()}

    @classmethod
    def get_amount_presets(cls) -> dict:
        return {key: name for key, (name, _) in cls.AMOUNT_PRESETS.items()}
