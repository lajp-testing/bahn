"""The quoter: the price of each option of a request. Owned by track 2 (quotes)."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .parts import Part

if TYPE_CHECKING:
    from .desk import Desk

DECLINE_FACTOR = 5  # a quote this many times the list price loses, and a lost quote costs nothing


def decline(request: dict[str, Any]) -> dict[str, int]:
    """A quote that loses: the way to decline a request without losing the dealer's goodwill."""
    first = request["options"][0]
    return {first["kind"]: first["listPriceCents"] * DECLINE_FACTOR}


class Quoter(Part):
    """The starter's quoter: a multiple of the list price. With `options="first"` it quotes the dealer's
    first option only, as the starter does; with `"all"`, every option."""

    def __init__(self, markup: float = 1.0, options: str = "first"):
        self.markup, self.options = markup, options

    def prices(self, request: dict[str, Any], desk: "Desk") -> dict[str, int]:
        offered = request["options"][:1] if self.options == "first" else request["options"]
        return {option["kind"]: round(option["listPriceCents"] * self.markup) for option in offered}
