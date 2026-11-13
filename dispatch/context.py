"""What the desk knows about a world before the week starts: its level, the map and the driver list."""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Context:
    level: int
    places: dict[str, dict[str, Any]] = field(default_factory=dict)  # place id -> { id, name, lat, lon }
    road_minutes: dict[tuple[str, str], int] = field(default_factory=dict)  # (from, to) -> minutes by car
    road_km: dict[tuple[str, str], float] = field(default_factory=dict)  # (from, to) -> km by road
    roster: list[dict[str, Any]] = field(default_factory=list)  # DriverProfile: id, homePlaceId, rating, licence, completedGigs, drops

    @classmethod
    def build(cls, level: int, world_map: dict[str, Any], roster: list[dict[str, Any]]) -> "Context":
        ctx = cls(level=level, roster=roster)
        ctx.places = {place["id"]: place for place in world_map["places"]}
        for road in world_map["roads"]:
            ctx.road_minutes[(road["from"], road["to"])] = road["minutes"]
            ctx.road_km[(road["from"], road["to"])] = road["km"]
        return ctx

    def minutes(self, a: str, b: str) -> int:
        return self.road_minutes[(a, b)]

    def km(self, a: str, b: str) -> float:
        return self.road_km[(a, b)]

    def straight_km(self, a: str, b: str) -> float:
        """The straight-line distance: notifications reach drivers within 30 km of a pickup, and an outage covers 80 km."""
        p, q = self.places[a], self.places[b]
        lat1, lat2 = math.radians(p["lat"]), math.radians(q["lat"])
        dlat, dlon = lat2 - lat1, math.radians(q["lon"] - p["lon"])
        h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        return 2 * 6371.0 * math.asin(math.sqrt(h))

    def drivers_at(self, place_id: str) -> list[dict[str, Any]]:
        return [driver for driver in self.roster if driver["homePlaceId"] == place_id]
