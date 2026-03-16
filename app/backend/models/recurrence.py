"""Recurrence model for recurring transactions."""

import calendar
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from models.transaction import Transaction, TransactionType


class Frequency(Enum):
    """Recurrence frequency options."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class Weekday(Enum):
    """Days of the week (matching Python's weekday() convention)."""

    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6


WEEKDAY_NAMES = {
    Weekday.MONDAY: "Mon",
    Weekday.TUESDAY: "Tue",
    Weekday.WEDNESDAY: "Wed",
    Weekday.THURSDAY: "Thu",
    Weekday.FRIDAY: "Fri",
    Weekday.SATURDAY: "Sat",
    Weekday.SUNDAY: "Sun",
}


class EndCondition(Enum):
    """How a recurring transaction ends."""

    NEVER = "never"
    ON_DATE = "on_date"
    AFTER_COUNT = "after_count"


DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


@dataclass
class RecurrenceRule:
    """Defines the recurrence pattern for a recurring transaction."""

    frequency: Frequency
    interval: int = 1
    end_condition: EndCondition = EndCondition.NEVER
    end_date: Optional[datetime] = None
    max_occurrences: Optional[int] = None
    weekdays: Set[Weekday] = field(default_factory=set)
    month_week: Optional[int] = None
    month_weekday: Optional[Weekday] = None

    def _next_daily(self, current: datetime) -> datetime:
        """Get the next occurrence for daily frequency."""
        return current + timedelta(days=self.interval)

    def _next_weekly_dates(
        self, current: datetime, rule_start: datetime
    ) -> List[datetime]:
        """Get next occurrence dates for weekly frequency within the same week cycle."""
        if not self.weekdays:
            return [current + timedelta(weeks=self.interval)]

        results = []
        # Find the start of the current interval week
        target_weekdays = sorted(self.weekdays, key=lambda w: w.value)

        # Check remaining days in current week
        for wd in target_weekdays:
            days_ahead = wd.value - current.weekday()
            if days_ahead > 0:
                candidate = current + timedelta(days=days_ahead)
                results.append(candidate)

        if not results:
            # Move to next interval week
            days_to_monday = 7 - current.weekday()
            next_week_start = current + timedelta(
                days=days_to_monday + (self.interval - 1) * 7
            )
            for wd in target_weekdays:
                candidate = next_week_start + timedelta(days=wd.value)
                results.append(candidate)

        return results

    def _nth_weekday_of_month(self, year: int, month: int) -> Optional[datetime]:
        """Get the Nth occurrence of a weekday in a given month."""
        if self.month_week is None or self.month_weekday is None:
            return None

        target_weekday = self.month_weekday.value
        first_day = datetime(year, month, 1)
        first_weekday = first_day.weekday()

        # Days until the first occurrence of target weekday
        days_until = (target_weekday - first_weekday) % 7
        first_occurrence_day = 1 + days_until

        # Nth occurrence
        nth_day = first_occurrence_day + (self.month_week - 1) * 7

        # Check if the day is valid for this month
        _, days_in_month = calendar.monthrange(year, month)
        if nth_day > days_in_month:
            return None

        return datetime(year, month, nth_day)

    def _next_month(self, year: int, month: int, steps: int = 1) -> tuple:
        """Advance month by steps, handling year rollover."""
        month += steps
        while month > 12:
            month -= 12
            year += 1
        return year, month

    def get_occurrences_in_range(
        self, start: datetime, end: datetime, rule_start: datetime
    ) -> List[datetime]:
        """Generate all occurrence dates between start and end.

        Args:
            start: Range start (inclusive).
            end: Range end (inclusive).
            rule_start: The original start date of the recurring transaction.

        Returns:
            Sorted list of occurrence datetimes within the range.
        """
        occurrences = []
        count = 0

        if self.frequency == Frequency.DAILY:
            current = rule_start
            while current <= end:
                if self._check_end(current, count):
                    break
                if current >= start:
                    occurrences.append(current)
                count += 1
                current = self._next_daily(current)

        elif self.frequency == Frequency.WEEKLY:
            if self.weekdays:
                # Generate week by week
                current_week_start = rule_start - timedelta(days=rule_start.weekday())
                target_weekdays = sorted(self.weekdays, key=lambda w: w.value)

                week = 0
                while True:
                    week_start = current_week_start + timedelta(
                        weeks=week * self.interval
                    )
                    if week_start > end + timedelta(days=7):
                        break

                    for wd in target_weekdays:
                        candidate = week_start + timedelta(days=wd.value)
                        candidate = candidate.replace(
                            hour=rule_start.hour,
                            minute=rule_start.minute,
                            second=rule_start.second,
                        )
                        if candidate < rule_start:
                            continue
                        if candidate > end:
                            continue
                        if self._check_end(candidate, count):
                            return sorted(occurrences)
                        if candidate >= start:
                            occurrences.append(candidate)
                        count += 1
                    week += 1
            else:
                current = rule_start
                while current <= end:
                    if self._check_end(current, count):
                        break
                    if current >= start:
                        occurrences.append(current)
                    count += 1
                    current += timedelta(weeks=self.interval)

        elif self.frequency == Frequency.MONTHLY:
            if self.month_week is not None and self.month_weekday is not None:
                # Nth weekday of month pattern
                year, month = rule_start.year, rule_start.month
                while True:
                    candidate = self._nth_weekday_of_month(year, month)
                    if candidate is not None:
                        candidate = candidate.replace(
                            hour=rule_start.hour,
                            minute=rule_start.minute,
                            second=rule_start.second,
                        )
                        if candidate > end:
                            break
                        if candidate >= rule_start:
                            if self._check_end(candidate, count):
                                break
                            if candidate >= start:
                                occurrences.append(candidate)
                            count += 1
                    year, month = self._next_month(year, month, self.interval)
                    if datetime(year, month, 1) > end:
                        break
            else:
                # Same day of month
                target_day = rule_start.day
                year, month = rule_start.year, rule_start.month
                while True:
                    _, days_in_month = calendar.monthrange(year, month)
                    day = min(target_day, days_in_month)
                    candidate = datetime(
                        year,
                        month,
                        day,
                        rule_start.hour,
                        rule_start.minute,
                        rule_start.second,
                    )
                    if candidate > end:
                        break
                    if candidate >= rule_start:
                        if self._check_end(candidate, count):
                            break
                        if candidate >= start:
                            occurrences.append(candidate)
                        count += 1
                    year, month = self._next_month(year, month, self.interval)

        elif self.frequency == Frequency.YEARLY:
            year = rule_start.year
            while True:
                month = rule_start.month
                _, days_in_month = calendar.monthrange(year, month)
                day = min(rule_start.day, days_in_month)
                candidate = datetime(
                    year,
                    month,
                    day,
                    rule_start.hour,
                    rule_start.minute,
                    rule_start.second,
                )
                if candidate > end:
                    break
                if candidate >= rule_start:
                    if self._check_end(candidate, count):
                        break
                    if candidate >= start:
                        occurrences.append(candidate)
                    count += 1
                year += self.interval

        return sorted(occurrences)

    def _check_end(self, current: datetime, count: int) -> bool:
        """Check if the recurrence has ended."""
        if self.end_condition == EndCondition.ON_DATE and self.end_date:
            if current > self.end_date:
                return True
        if self.end_condition == EndCondition.AFTER_COUNT and self.max_occurrences:
            if count >= self.max_occurrences:
                return True
        return False

    def description(self) -> str:
        """Return a human-readable description of the recurrence rule."""
        parts = []

        if self.frequency == Frequency.DAILY:
            if self.interval == 1:
                parts.append("Daily")
            else:
                parts.append(f"Every {self.interval} days")
        elif self.frequency == Frequency.WEEKLY:
            if self.interval == 1:
                parts.append("Weekly")
            else:
                parts.append(f"Every {self.interval} weeks")
            if self.weekdays:
                day_names = [
                    WEEKDAY_NAMES[wd]
                    for wd in sorted(self.weekdays, key=lambda w: w.value)
                ]
                parts.append(f"on {', '.join(day_names)}")
        elif self.frequency == Frequency.MONTHLY:
            if self.interval == 1:
                parts.append("Monthly")
            else:
                parts.append(f"Every {self.interval} months")
            if self.month_week is not None and self.month_weekday is not None:
                ordinals = {1: "1st", 2: "2nd", 3: "3rd", 4: "4th", 5: "5th"}
                ordinal = ordinals.get(self.month_week, f"{self.month_week}th")
                day_name = WEEKDAY_NAMES[self.month_weekday]
                parts.append(f"on the {ordinal} {day_name}")
        elif self.frequency == Frequency.YEARLY:
            if self.interval == 1:
                parts.append("Yearly")
            else:
                parts.append(f"Every {self.interval} years")

        # End condition
        if self.end_condition == EndCondition.ON_DATE and self.end_date:
            parts.append(f"until {self.end_date.strftime('%Y-%m-%d')}")
        elif self.end_condition == EndCondition.AFTER_COUNT and self.max_occurrences:
            parts.append(f"for {self.max_occurrences} occurrences")

        return " ".join(parts)

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> "RecurrenceRule":
        """Deserialize a RecurrenceRule from a JSON-compatible dict."""
        return cls(
            frequency=Frequency(data["frequency"]),
            interval=data.get("interval", 1),
            end_condition=EndCondition(
                data.get("end_condition", EndCondition.NEVER.value)
            ),
            end_date=(
                datetime.strptime(data["end_date"], DATETIME_FORMAT)
                if data.get("end_date")
                else None
            ),
            max_occurrences=data.get("max_occurrences"),
            weekdays=set(Weekday(wd) for wd in data.get("weekdays", [])),
            month_week=data.get("month_week"),
            month_weekday=(
                Weekday(data["month_weekday"])
                if data.get("month_weekday") is not None
                else None
            ),
        )

    def to_json(self) -> Dict[str, Any]:
        """Serialize the recurrence rule to a JSON-compatible dict."""
        return {
            "frequency": self.frequency.value,
            "interval": self.interval,
            "end_condition": self.end_condition.value,
            "end_date": (
                self.end_date.strftime(DATETIME_FORMAT) if self.end_date else None
            ),
            "max_occurrences": self.max_occurrences,
            "weekdays": [wd.value for wd in self.weekdays],
            "month_week": self.month_week,
            "month_weekday": (
                self.month_weekday.value if self.month_weekday is not None else None
            ),
        }


@dataclass
class RecurringTransaction:
    """Template for a recurring transaction that generates concrete transactions.

    When ``target_wallet_name`` is set the recurring entry represents a
    *recurring transfer* (or recurring goal save) and the scheduler will call
    ``wallet_manager.transfer()`` instead of adding a plain transaction.
    """

    amount: float
    transaction_type: TransactionType
    category: str
    description: str
    recurrence_rule: RecurrenceRule
    start_date: datetime
    wallet_name: str
    id: str = field(default_factory=lambda: "rec-" + str(uuid.uuid4())[:8])
    is_active: bool = True
    generated_count: int = 0
    last_generated: Optional[datetime] = None
    exceptions: Set[datetime] = field(default_factory=set)
    target_wallet_name: Optional[str] = None
    received_amount: Optional[float] = None

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> Optional["RecurringTransaction"]:
        """Deserialize a RecurringTransaction from a JSON-compatible dict."""
        required = {
            "amount",
            "transaction_type",
            "category",
            "recurrence_rule",
            "start_date",
            "wallet_name",
        }
        if not required.issubset(data.keys()):
            return None

        return cls(
            amount=float(data["amount"]),
            transaction_type=TransactionType(data["transaction_type"]),
            category=data["category"],
            description=data["description"],
            recurrence_rule=RecurrenceRule.from_json(data["recurrence_rule"]),
            start_date=datetime.strptime(data["start_date"], DATETIME_FORMAT),
            wallet_name=data["wallet_name"],
            id=data["id"],
            is_active=bool(data["is_active"]),
            generated_count=int(data["generated_count"]),
            last_generated=(
                datetime.strptime(data["last_generated"], DATETIME_FORMAT)
                if data["last_generated"]
                else None
            ),
            exceptions=set(
                datetime.strptime(dt, DATETIME_FORMAT)
                for dt in data.get("exceptions", [])
            ),
            target_wallet_name=data.get("target_wallet_name"),
            received_amount=(
                float(data["received_amount"])
                if data.get("received_amount") is not None
                else None
            ),
        )

    def to_json(self) -> Dict[str, Any]:
        """Serialize this RecurringTransaction to a JSON-compatible dict."""
        return {
            "amount": self.amount,
            "transaction_type": self.transaction_type.value,
            "category": self.category,
            "description": self.description,
            "recurrence_rule": self.recurrence_rule.to_json(),
            "start_date": self.start_date.strftime(DATETIME_FORMAT),
            "wallet_name": self.wallet_name,
            "id": self.id,
            "is_active": self.is_active,
            "generated_count": self.generated_count,
            "last_generated": (
                self.last_generated.strftime(DATETIME_FORMAT)
                if self.last_generated
                else None
            ),
            "exceptions": [
                dt.strftime(DATETIME_FORMAT) for dt in sorted(self.exceptions)
            ],
            "target_wallet_name": self.target_wallet_name,
            "received_amount": self.received_amount,
        }

    def create_transaction(self, date: datetime) -> Transaction:
        """Create a concrete Transaction from this template for a given date."""
        return Transaction(
            amount=self.amount,
            transaction_type=self.transaction_type,
            category=self.category,
            description=self.description,
            datetime_created=date,
            recurrence_id=self.id,
        )

    @property
    def is_transfer(self) -> bool:
        """True when this recurring entry represents a transfer."""
        return self.target_wallet_name is not None

    def summary_str(self) -> str:
        """Return a short summary string."""
        sign = "+" if self.transaction_type == TransactionType.INCOME else "-"
        status = "Active" if self.is_active else "Paused"
        if self.is_transfer:
            return (
                f"[{status}] Transfer {self.wallet_name} -> "
                f"{self.target_wallet_name} {sign}{abs(self.amount):.2f} "
                f"({self.recurrence_rule.description()})"
            )
        return (
            f"[{status}] {self.category} - {sign}{abs(self.amount):.2f} "
            f"({self.recurrence_rule.description()})"
        )

    def detailed_str(self) -> str:
        """Return a detailed string representation."""
        sign = "+" if self.transaction_type == TransactionType.INCOME else "-"
        status = "Active" if self.is_active else "Paused"
        if self.is_transfer:
            type_name = "Recurring Transfer"
        elif self.transaction_type == TransactionType.INCOME:
            type_name = "Income"
        else:
            type_name = "Expense"

        lines = [
            f"ID: {self.id}",
            f"Status: {status}",
            f"Type: {type_name}",
            f"Amount: {sign}{abs(self.amount):.2f}",
            f"Category: {self.category}",
            f"Description: {self.description or 'N/A'}",
            f"Wallet: {self.wallet_name}",
        ]
        if self.is_transfer:
            lines.append(f"Target Wallet: {self.target_wallet_name}")
        lines.extend(
            [
                f"Pattern: {self.recurrence_rule.description()}",
                f"Start Date: {self.start_date.strftime('%Y-%m-%d')}",
                f"Generated: {self.generated_count} transactions",
            ]
        )

        if self.last_generated:
            lines.append(f"Last Generated: {self.last_generated.strftime('%Y-%m-%d')}")

        if self.exceptions:
            exc_dates = sorted(self.exceptions)
            exc_strs = [d.strftime("%Y-%m-%d") for d in exc_dates[:5]]
            if len(exc_dates) > 5:
                exc_strs.append(f"... +{len(exc_dates) - 5} more")
            lines.append(f"Skipped Dates: {', '.join(exc_strs)}")

        return "\n".join(lines)
