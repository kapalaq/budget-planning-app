"""Currency exchange rate service for portfolio aggregation."""

import logging
import os
import time
from typing import Dict, Optional

import aiohttp

logger = logging.getLogger(__name__)

# Free API — no key required, 1500 requests/month
_API_URL = os.getenv("CURRENCY_API_URL")
_CACHE_TTL = 14400  # 4 hour


class CurrencyService:
    """Fetches and caches exchange rates for cross-currency portfolio totals."""

    def __init__(self):
        self._rates: Dict[str, Dict[str, float]] = {}
        self._timestamps: Dict[str, float] = {}

    async def get_rates(self, base: str = "USD") -> Optional[Dict[str, float]]:
        """Get exchange rates for a base currency. Returns {currency: rate} or None."""
        base = base.upper()
        now = time.time()

        # Return cached if fresh
        if base in self._rates and (now - self._timestamps.get(base, 0)) < _CACHE_TTL:
            return self._rates[base]

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    _API_URL.format(base=base), timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get("result") == "success":
                            self._rates[base] = data["rates"]
                            self._timestamps[base] = now
                            return self._rates[base]
        except Exception as e:
            logger.warning("Currency API error: %s", e)

        # Return stale cache if available
        return self._rates.get(base)

    async def convert(
        self, amount: float, from_currency: str, to_currency: str
    ) -> Optional[float]:
        """Convert amount between currencies. Returns None if rates unavailable."""
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()

        if from_currency == to_currency:
            return amount

        rates = await self.get_rates(from_currency)
        if rates and to_currency in rates:
            return amount * rates[to_currency]
        return None


# Singleton instance
currency_service = CurrencyService()
