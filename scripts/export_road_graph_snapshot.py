"""Offline-only exporter for the reviewed curated demo road graph.

Runtime never calls a network provider. Run this script only when the packaged
graph is deliberately reviewed and versioned.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.services.road_graph_router import RoadGraphRouter  # noqa: E402


def main() -> None:
    graph = {
        "metadata": {
            "graph_id": "op1-pedestrian-demo-v1",
            "graph_version": "1.0.0",
            "source": "curated_demo_graph",
            "snapshot_at": None,
            "license": "AirGuard educational demo data",
            "attribution": "AirGuard curated demo graph",
            "extent": {
                "south": 20.9875,
                "west": 105.9350,
                "north": 21.0025,
                "east": 105.9615,
            },
            "boundary": [
                [20.9875, 105.9350],
                [21.0025, 105.9350],
                [21.0025, 105.9615],
                [20.9875, 105.9615],
                [20.9875, 105.9350],
            ],
        },
        "station_coordinates": RoadGraphRouter.STATION_COORDINATES,
        "nodes": RoadGraphRouter.NODES,
        "edges": RoadGraphRouter.EDGES,
        "circuits": RoadGraphRouter.CANONICAL_CIRCUITS,
    }
    canonical = json.dumps(graph, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    graph["metadata"]["checksum_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    destination = ROOT / "data" / "ocean-park-1-road-graph.json"
    destination.write_text(json.dumps(graph, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(destination)


if __name__ == "__main__":
    main()
