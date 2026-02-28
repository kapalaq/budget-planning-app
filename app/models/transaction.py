"""Transaction model representing a single financial transaction."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from wallet.wallet import Wallet


class TransactionType(Enum):
    """Enum representing transaction types."""

    INCOME = "+"
    EXPENSE = "-"


@dataclass
class Transaction:
    """Represents a single financial transaction."""

    amount: float
    transaction_type: TransactionType
    category: str
    description: str = ""
    datetime_created: datetime = field(default_factory=datetime.now)
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    recurrence_id: Optional[str] = None
    __is_transfer: bool = False

    @property
    def signed_amount(self) -> float:
        """Return amount with sign based on transaction type."""
        if self.transaction_type == TransactionType.EXPENSE:
            return -abs(self.amount)
        return abs(self.amount)

    def __str__(self) -> str:
        sign = "+" if self.transaction_type == TransactionType.INCOME else "-"
        return f"{self.category} - {sign}{abs(self.amount):.2f}"

    def get_transfer(self):
        """Return True if Transaction is a Transfer transaction"""
        return self.__is_transfer

    def update(self, transaction: "Transaction") -> bool:
        """Updates attributes of this transaction."""
        try:
            new_attrs = vars(transaction)
            for attr_name, attr_val in vars(self).items():
                if not attr_name.startswith("_"):
                    setattr(self, attr_name, new_attrs.get(attr_name, attr_val))
            return True
        except Exception as e:
            print(f"Error updating transaction: {e}")
            return False

    def detailed_str(self) -> str:
        """Return detailed string representation."""
        sign = "+" if self.transaction_type == TransactionType.INCOME else "-"
        type_label = (
            "Income" if self.transaction_type == TransactionType.INCOME else "Expense"
        )
        if self.recurrence_id:
            type_label += " (Recurring)"
        return (
            f"ID: {self.id}\n"
            f"Type: {self.transaction_type.value} ({type_label})\n"
            f"Amount: {sign}{abs(self.amount):.2f}\n"
            f"Category: {self.category}\n"
            f"Description: {self.description or 'N/A'}\n"
            f"Date: {self.datetime_created.strftime('%Y-%m-%d %H:%M:%S')}"
        )


@dataclass
class Transfer(Transaction):
    """Represents a single transfer transaction between wallets."""

    source: "Wallet" = field(
        default=None,
        metadata={
            "description": "Reference on wallet that this transfer transaction belongs to."
        },
    )
    connected: "Transfer" = field(
        default=None,
        metadata={"description": "Reference on connected transaction entity."},
    )
    _is_transfer: bool = field(default=True, repr=False)
    _syncing: bool = field(default=False, repr=False)

    def __post_init__(self):
        """Ensure category is always 'Transfer'."""
        self.category = "Transfer"

    def get_transfer(self):
        """Return True if Transaction is a Transfer transaction."""
        return True

    def synchronise(self) -> None:
        """Synchronize this transfer with its connected counterpart."""
        if self.connected is not None and not self._syncing:
            self._syncing = True
            try:
                self.connected.amount = self.amount
                # Flip the transaction type for the connected side
                self.connected.transaction_type = (
                    TransactionType.INCOME
                    if self.transaction_type == TransactionType.EXPENSE
                    else TransactionType.EXPENSE
                )
                self.connected.description = self.description
                self.connected.datetime_created = self.datetime_created
            finally:
                self._syncing = False

    def update(self, transaction: "Transaction") -> bool:
        """Updates attributes of this transaction and syncs with connected."""
        try:
            # Update amount if provided
            if hasattr(transaction, "amount"):
                self.amount = transaction.amount
            # Update description if provided
            if hasattr(transaction, "description"):
                self.description = transaction.description
            # Update datetime if provided
            if hasattr(transaction, "datetime_created"):
                self.datetime_created = transaction.datetime_created
            # Category stays as "Transfer" - ignore any category changes
            self.category = "Transfer"
            # Synchronize with connected transfer
            self.synchronise()
            return True
        except Exception as e:
            print(f"Error updating transfer: {e}")
            return False

    def detailed_str(self) -> str:
        """Return detailed string representation."""
        sign = "+" if self.transaction_type == TransactionType.INCOME else "-"
        # Determine source and target wallet names
        if self.transaction_type == TransactionType.EXPENSE:
            from_wallet = self.source.name if self.source else "Unknown"
            to_wallet = (
                self.connected.source.name
                if self.connected and self.connected.source
                else "Unknown"
            )
        else:
            from_wallet = (
                self.connected.source.name
                if self.connected and self.connected.source
                else "Unknown"
            )
            to_wallet = self.source.name if self.source else "Unknown"

        return (
            f"ID: {self.id}\n"
            f"Type: Transfer ({'Outgoing' if self.transaction_type == TransactionType.EXPENSE else 'Incoming'})\n"
            f"Amount: {sign}{abs(self.amount):.2f}\n"
            f"From: {from_wallet}\n"
            f"To: {to_wallet}\n"
            f"Description: {self.description or 'N/A'}\n"
            f"Date: {self.datetime_created.strftime('%Y-%m-%d %H:%M:%S')}"
        )

    def __str__(self) -> str:
        """Return string representation."""
        sign = "+" if self.transaction_type == TransactionType.INCOME else "-"
        if self.transaction_type == TransactionType.EXPENSE:
            target = (
                self.connected.source.name
                if self.connected and self.connected.source
                else "?"
            )
            return f"Transfer to {target} - {sign}{abs(self.amount):.2f}"
        else:
            source = (
                self.connected.source.name
                if self.connected and self.connected.source
                else "?"
            )
            return f"Transfer from {source} - {sign}{abs(self.amount):.2f}"
