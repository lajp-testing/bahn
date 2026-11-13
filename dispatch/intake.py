"""The intake: how much work to take. Owned by track 1 (intake and on-time).

It sees the quoter's prices for a request and returns the prices to send: the same, higher, or a
decline (`dispatch.quote.decline`). An empty answer sends no quote, which costs a little goodwill.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .parts import Part

if TYPE_CHECKING:
    from .desk import Desk


class Intake(Part):
    """The starter's intake: take everything."""

    def admit(self, request: dict[str, Any], prices: dict[str, int], desk: "Desk") -> dict[str, int]:
        return prices
