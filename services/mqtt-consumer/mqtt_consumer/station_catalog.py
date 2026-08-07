from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class StationCatalog:
    def __init__(self, stations: dict[str, dict[str, Any]]) -> None:
        self._stations = stations

    @classmethod
    def load(cls, path: Path) -> "StationCatalog":
        with path.open("r", encoding="utf-8") as file:
            items = json.load(file)
        stations = {item["station_id"]: item for item in items if item.get("station_id")}
        return cls(stations)

    def has_station(self, station_id: str) -> bool:
        return station_id in self._stations

    def stations(self) -> list[dict[str, Any]]:
        return list(self._stations.values())
