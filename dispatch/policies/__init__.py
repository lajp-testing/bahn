"""A policy is one choice of the four parts. Each module here has `build(ctx, **params) -> Parts`.

    load("base")(ctx)                     the kit starter's behaviour
    load("base")(ctx, markup=1.3)         the same with a parameter changed
"""
from __future__ import annotations

import importlib
from typing import Any, Callable

from ..context import Context
from ..parts import Parts


def load(name: str) -> Callable[..., Parts]:
    return importlib.import_module(f"{__name__}.{name}").build


def parse_params(pairs: list[str]) -> dict[str, Any]:
    """`["markup=1.3", "options=all"]` -> `{"markup": 1.3, "options": "all"}`."""
    params: dict[str, Any] = {}
    for pair in pairs:
        key, _, text = pair.partition("=")
        value: Any = text
        for cast in (int, float):
            try:
                value = cast(text)
                break
            except ValueError:
                pass
        if text in ("true", "false"):
            value = text == "true"
        params[key] = value
    return params


__all__ = ["load", "parse_params", "Context", "Parts"]
