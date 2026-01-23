"""Transaction model representing a single financial transaction."""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, TYPE_CHECKING
import uuid

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
        return (
            f"ID: {self.id}\n"
            f"Type: {self.transaction_type.value} ({'Income' if self.transaction_type == TransactionType.INCOME else 'Expense'})\n"
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
        metadata={"description": "Reference on wallet that this transfer transaction belongs to."}
    )
    connected: "Transfer" = field(
        default=None,
        metadata={"description": "Reference on connected transaction entity."}
    )
    __is_transfer: bool = True

    def synchronise(self) -> None:
        if self.connected is not None:
            self.connected.amount = -self.amount
            self.connected.transaction_type = TransactionType.INCOME if self.transaction_type == TransactionType.EXPENSE else TransactionType.EXPENSE
            self.connected.category = self.category
            self.connected.description = self.description
            self.connected.datetime_created = self.datetime_created

    def update(self, transaction: "Transfer") -> bool:
        """Updates attributes of this transaction."""
        try:
            new_attrs = vars(transaction)
            for attr_name, attr_val in vars(self).items():
                if not attr_name.startswith("_"):
                    setattr(self, attr_name, new_attrs.get(attr_name, attr_val))
            return True
        except Exception as e:
            print(f"Error updating transfer: {e}")
            return False

    def detailed_str(self) -> str:
        """Return detailed string representation."""
        sign = "+" if self.transaction_type == TransactionType.INCOME else "-"
        return (
            f"ID: {self.id}\n"
            f"Type: Transfer ({'Income' if self.transaction_type == TransactionType.INCOME else 'Expense'})\n"
            f"Amount: {sign}{abs(self.amount):.2f}\n"
            f"From {self.source} -> To {self.connected.source}\n"
            f"Category: {self.category}\n"
            f"Description: {self.description or 'N/A'}\n"
            f"Date: {self.datetime_created.strftime('%Y-%m-%d %H:%M:%S')}"
        )

    def __del__(self):
        """Destructor."""
        if self.source.get_transaction(self.id) is not None:
            self.source.delete_transaction(self.id)
        elif self.connected is not None:
            self.connected.connected = None
