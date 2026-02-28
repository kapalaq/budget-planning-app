"""Category management for transactions."""

from typing import Set

from models.transaction import TransactionType

# Reserved category name for transfers - cannot be used for regular transactions
TRANSFER_CATEGORY = "Transfer"


class CategoryManager:
    """Manages categories for income and expense transactions separately."""

    def __init__(self):
        self._income_categories: Set[str] = set()
        self._expense_categories: Set[str] = set()
        self._initialize_default_categories()

    def _initialize_default_categories(self):
        """Initialize with some default categories."""
        self._income_categories = {"Salary", "Freelance", "Investment", "Gift", "Other"}
        self._expense_categories = {
            "Food",
            "Transport",
            "Entertainment",
            "Bills",
            "Shopping",
            "Health",
            "Other",
        }

    def get_categories(self, transaction_type: TransactionType) -> Set[str]:
        """Get categories for a specific transaction type (excludes Transfer)."""
        if transaction_type == TransactionType.INCOME:
            return self._income_categories.copy() - {TRANSFER_CATEGORY}
        return self._expense_categories.copy() - {TRANSFER_CATEGORY}

    def add_category(self, category: str, transaction_type: TransactionType) -> None:
        """Add a new category for a specific transaction type."""
        if transaction_type == TransactionType.INCOME:
            self._income_categories.add(category)
        else:
            self._expense_categories.add(category)

    def category_exists(self, category: str, transaction_type: TransactionType) -> bool:
        """Check if a category exists for a transaction type."""
        categories = self.get_categories(transaction_type)
        return category in categories

    def is_reserved_category(self, category: str) -> bool:
        """Check if a category is reserved (e.g., Transfer)."""
        return category == TRANSFER_CATEGORY
