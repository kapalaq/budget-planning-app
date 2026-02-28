"""Recurrence scheduler that materializes recurring transactions."""

from datetime import datetime
from typing import TYPE_CHECKING, Dict, List, Optional

from models.recurrence import RecurringTransaction

if TYPE_CHECKING:
    from wallet.wallet_manager import WalletManager


class RecurrenceScheduler:
    """Materializes recurring transactions into concrete wallet transactions."""

    def __init__(self, wallet_manager: "WalletManager"):
        self._recurring_transactions: Dict[str, RecurringTransaction] = {}
        self._wallet_manager = wallet_manager

    def add_recurring(self, recurring: RecurringTransaction) -> None:
        """Add a recurring transaction template."""
        self._recurring_transactions[recurring.id] = recurring

    def remove_recurring(self, recurring_id: str) -> Optional[RecurringTransaction]:
        """Remove a recurring transaction template by ID."""
        return self._recurring_transactions.pop(recurring_id, None)

    def get_recurring(self, recurring_id: str) -> Optional[RecurringTransaction]:
        """Get a recurring transaction by ID."""
        return self._recurring_transactions.get(recurring_id)

    def get_all_recurring(self) -> List[RecurringTransaction]:
        """Get all recurring transactions."""
        return list(self._recurring_transactions.values())

    def get_recurring_for_wallet(self, wallet_name: str) -> List[RecurringTransaction]:
        """Get all recurring transactions for a specific wallet."""
        return [
            r
            for r in self._recurring_transactions.values()
            if r.wallet_name.lower() == wallet_name.lower()
        ]

    def get_recurring_by_index(self, index: int) -> Optional[RecurringTransaction]:
        """Get a recurring transaction by its 1-based display index."""
        all_recurring = self.get_all_recurring()
        if 1 <= index <= len(all_recurring):
            return all_recurring[index - 1]
        return None

    def process_due_transactions(self) -> int:
        """Materialize all due recurring transactions up to now.

        Returns the number of transactions generated.
        """
        now = datetime.now()
        total_generated = 0

        for recurring in self._recurring_transactions.values():
            if not recurring.is_active:
                continue

            wallet = self._wallet_manager.get_wallet(recurring.wallet_name)
            if wallet is None:
                continue

            # Determine the range start
            if recurring.last_generated:
                range_start = recurring.last_generated
            else:
                range_start = recurring.start_date

            # Get all occurrences in the range
            occurrences = recurring.recurrence_rule.get_occurrences_in_range(
                start=range_start, end=now, rule_start=recurring.start_date
            )

            for occ_date in occurrences:
                # Skip if this date was already generated or is an exception
                if recurring.last_generated and occ_date <= recurring.last_generated:
                    continue

                # Normalize exception dates for comparison
                occ_date_normalized = occ_date.replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
                if any(
                    exc.replace(hour=0, minute=0, second=0, microsecond=0)
                    == occ_date_normalized
                    for exc in recurring.exceptions
                ):
                    continue

                # Create and add the transaction
                transaction = recurring.create_transaction(occ_date)
                wallet.add_transaction(transaction)

                recurring.generated_count += 1
                recurring.last_generated = occ_date
                total_generated += 1

        return total_generated

    def deactivate_recurring(self, recurring_id: str) -> bool:
        """Pause a recurring transaction."""
        recurring = self._recurring_transactions.get(recurring_id)
        if recurring:
            recurring.is_active = False
            return True
        return False

    def activate_recurring(self, recurring_id: str) -> bool:
        """Resume a recurring transaction."""
        recurring = self._recurring_transactions.get(recurring_id)
        if recurring:
            recurring.is_active = True
            return True
        return False

    def remove_recurring_for_wallet(self, wallet_name: str) -> int:
        """Remove all recurring transactions for a wallet.

        Returns the number of removed recurring transactions.
        """
        to_remove = [
            rid
            for rid, r in self._recurring_transactions.items()
            if r.wallet_name.lower() == wallet_name.lower()
        ]
        for rid in to_remove:
            del self._recurring_transactions[rid]
        return len(to_remove)
