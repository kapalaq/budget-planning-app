"""Recurrence model for recurring transactions."""
import calendar
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional, Set

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
        current_weekday = Weekday(current.weekday())
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
                current_week_start = rule_start - timedelta(
                    days=rule_start.weekday()
                )
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


@dataclass
class RecurringTransaction:
    """Template for a recurring transaction that generates concrete transactions."""

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

    def summary_str(self) -> str:
        """Return a short summary string."""
        sign = "+" if self.transaction_type == TransactionType.INCOME else "-"
        status = "Active" if self.is_active else "Paused"
        return (
            f"[{status}] {self.category} - {sign}{abs(self.amount):.2f} "
            f"({self.recurrence_rule.description()})"
        )

    def detailed_str(self) -> str:
        """Return a detailed string representation."""
        sign = "+" if self.transaction_type == TransactionType.INCOME else "-"
        status = "Active" if self.is_active else "Paused"
        type_name = "Income" if self.transaction_type == TransactionType.INCOME else "Expense"

        lines = [
            f"ID: {self.id}",
            f"Status: {status}",
            f"Type: {type_name}",
            f"Amount: {sign}{abs(self.amount):.2f}",
            f"Category: {self.category}",
            f"Description: {self.description or 'N/A'}",
            f"Wallet: {self.wallet_name}",
            f"Pattern: {self.recurrence_rule.description()}",
            f"Start Date: {self.start_date.strftime('%Y-%m-%d')}",
            f"Generated: {self.generated_count} transactions",
        ]

        if self.last_generated:
            lines.append(
                f"Last Generated: {self.last_generated.strftime('%Y-%m-%d')}"
            )

        if self.exceptions:
            exc_dates = sorted(self.exceptions)
            exc_strs = [d.strftime("%Y-%m-%d") for d in exc_dates[:5]]
            if len(exc_dates) > 5:
                exc_strs.append(f"... +{len(exc_dates) - 5} more")
            lines.append(f"Skipped Dates: {', '.join(exc_strs)}")

        return "\n".join(lines)
