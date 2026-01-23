"""Wallet class that manages all transactions."""
import uuid
from datetime import datetime
from typing import List, Dict, Optional
from functools import singledispatchmethod
from collections import defaultdict

from models.transaction import Transaction, TransactionType
from models.category import CategoryManager
from strategies.sorting import SortingContext


class Wallet:
    """Main wallet class that holds and manages all transactions."""
    
    def __init__(self, name: str, starting_value: float = None, currency: str = 'KZT', description: str = ''):
        """
        Args:
            :param name: Name of the wallet.
            :param starting_value: A value that will present on the wallet from the beginning.
            :param currency: Currency of the wallet.
            :param description: Description of the wallet.
        """
        # Important
        self.id = str(uuid.uuid4())[:8]
        self.name = name
        self.currency = currency
        self.__transactions: Dict[str, Transaction] = {}
        self.__category_manager = CategoryManager()
        self.__sorting_context = SortingContext()

        # Optional
        self.description = description
        self.total_expense: float = 0.0
        self.total_income: float = 0.0
        self.balance: float = 0.0
        self.datetime_created: datetime =datetime.now()

        if starting_value is not None:
            initial_transaction = Transaction(
                amount=starting_value,
                transaction_type=TransactionType.INCOME,
                category='Перенос остатка'
            )
            self.__transactions[initial_transaction.id] = initial_transaction

    @property
    def category_manager(self) -> CategoryManager:
        return self.__category_manager
    
    @property
    def sorting_context(self) -> SortingContext:
        return self.__sorting_context

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
            transaction.category, 
            transaction.transaction_type
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

    def update_transaction(self, index: Optional[int|str], updated: Transaction) -> bool:
        """Update a transaction by its display index or ID."""
        old_transaction = self.get_transaction(index)

        if old_transaction is not None:
            self.__del_total(old_transaction)
            self.__add_total(updated)

            return old_transaction.update(updated)
        return False

    def delete_transaction(self, index: Optional[int|str]) -> bool:
        """Delete a transaction by its display index or ID."""
        transaction_to_delete = self.get_transaction(index)
        if transaction_to_delete is not None:
            self.__del_total(transaction_to_delete)
            self.__transactions.pop(transaction_to_delete.id, None)
            del transaction_to_delete

            return True
        return False

    def get_sorted_transactions(self) -> List[Transaction]:
        """Get all transactions sorted by current strategy."""
        return self.__sorting_context.sort(self.__transactions.values())
    
    def get_category_totals(self) -> Dict[str, float]:
        """Get total amount per category (only non-zero)."""
        totals: Dict[str, float] = defaultdict(float)
        for t in self.__transactions.values():
            totals[t.category] += t.signed_amount
        return {k: v for k, v in totals.items() if v != 0}

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

    def transaction_count(self) -> int:
        """Return the number of transactions."""
        return len(self.__transactions)

    def __del__(self):
        """Destructor of a wallet."""
        for transaction in self.__transactions.values():
            self.delete_transaction(transaction.id)
        del self.__transactions
