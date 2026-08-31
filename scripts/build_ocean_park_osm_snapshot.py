"""Build the checked-in Ocean Park 1 pedestrian graph from OpenStreetMap.

This is an explicit maintenance command, never a runtime dependency.  Runtime
routing reads only the generated JSON snapshot and verifies its checksum.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


BOUNDARY = [
    [21.0047847, 105.9477604],
    [20.9933962, 105.9628773],
    [20.9890436, 105.9600712],
    [20.9852230, 105.9518985],
    [20.9840728, 105.9509930],
    [20.9851752, 105.9432602],
    [20.9921545, 105.9371584],
    [20.9968500, 105.9334673],
    [20.9980664, 105.9352872],
    [21.0017814, 105.9420739],
]
STATIONS = {
    "S01": [21.0008, 105.9428],
    "S02": [20.9975, 105.9430],
    "S03": [20.9953, 105.9500],
    "S04": [20.9898, 105.9467],
    "S05": [20.9910, 105.9560],
}
WALKABLE_HIGHWAYS = {
    "bridleway",
    "cycleway",
    "footway",
    "living_street",
    "path",
    "pedestrian",
    "residential",
    "road",
    "secondary",
    "secondary_link",
    "service",
    "steps",
    "tertiary",
    "tertiary_link",
    "track",
    "unclassified",
}
POI_KEYS = ("amenity", "leisure", "tourism", "shop", "office", "healthcare", "sport")
OVERPASS_URL = "https://overpass-api.de/api/interpreter"


def inside_boundary(lat: float, lon: float) -> bool:
    inside = False
    j = len(BOUNDARY) - 1
    for i, (yi, xi) in enumerate(BOUNDARY):
        yj, xj = BOUNDARY[j]
        if (yi > lat) != (yj > lat) and lon < (xj - xi) * (lat - yi) / ((yj - yi) or 1e-12) + xi:
            inside = not inside
        j = i
    return inside


def query_text() -> str:
    south = min(point[0] for point in BOUNDARY)
    west = min(point[1] for point in BOUNDARY)
    north = max(point[0] for point in BOUNDARY)
    east = max(point[1] for point in BOUNDARY)
    bbox = f"{south},{west},{north},{east}"
    poi_queries = "\n".join(f'  nwr["name"]["{key}"]({bbox});' for key in POI_KEYS)
    return f"""[out:json][timeout:120];
(
  way["highway"]({bbox});
{poi_queries}
);
out geom;
"""


def fetch_overpass() -> dict[str, Any]:
    request = urllib.request.Request(
        OVERPASS_URL,
        data=urllib.parse.urlencode({"data": query_text()}).encode("utf-8"),
        headers={"User-Agent": "AirGuard-AI-educational-snapshot/1.0"},
    )
    with urllib.request.urlopen(request, timeout=180) as response:
        return json.load(response)


def walkable(tags: dict[str, Any]) -> bool:
    highway = str(tags.get("highway") or "")
    if highway not in WALKABLE_HIGHWAYS:
        return False
    if str(tags.get("foot") or "").lower() in {"no", "private"}:
        return False
    if str(tags.get("access") or "").lower() in {"no", "private"} and str(tags.get("foot") or "").lower() not in {
        "yes",
        "designated",
        "permissive",
    }:
        return False
    return True


def build_graph(raw: dict[str, Any], snapshot_at: str) -> dict[str, Any]:
    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, Any]] = []
    pois: list[dict[str, Any]] = []
    edge_ids: set[str] = set()

    for element in raw.get("elements") or []:
        tags = dict(element.get("tags") or {})
        geometry = element.get("geometry") or []
        if element.get("type") == "way" and walkable(tags) and len(geometry) >= 2:
            osm_node_ids = element.get("nodes") or []
            if len(osm_node_ids) != len(geometry):
                continue
            for index, (first, second) in enumerate(zip(geometry, geometry[1:])):
                a = [float(first["lat"]), float(first["lon"])]
                b = [float(second["lat"]), float(second["lon"])]
                midpoint = [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2]
                if not inside_boundary(midpoint[0], midpoint[1]):
                    continue
                from_id = f"OSM_N_{osm_node_ids[index]}"
                to_id = f"OSM_N_{osm_node_ids[index + 1]}"
                nodes.setdefault(from_id, {"id": from_id, "name": tags.get("name") or from_id, "lat": a[0], "lng": a[1], "zone": "ocean_park_1"})
                nodes.setdefault(to_id, {"id": to_id, "name": tags.get("name") or to_id, "lat": b[0], "lng": b[1], "zone": "ocean_park_1"})
                edge_id = f"osm_way_{element['id']}_{index}"
                if edge_id in edge_ids:
                    continue
                edge_ids.add(edge_id)
                foot_only = str(tags.get("highway")) in {"footway", "path", "pedestrian", "steps"}
                edges.append(
                    {
                        "id": edge_id,
                        "from": from_id,
                        "to": to_id,
                        "sensor_id": None,
                        "name": tags.get("name") or f"OSM way {element['id']}",
                        "surface": tags.get("surface") or "unknown",
                        "road_type": tags.get("highway"),
                        "highway": tags.get("highway"),
                        "access": {
                            "foot": True,
                            "bicycle": str(tags.get("bicycle") or "").lower() != "no" and str(tags.get("highway")) != "steps",
                            "motor_vehicle": not foot_only and str(tags.get("motor_vehicle") or "").lower() != "no",
                        },
                        "traffic_conflict": "low" if foot_only else "mixed",
                        "osm_way_id": int(element["id"]),
                        "coords": [a, b],
                    }
                )

        name = str(tags.get("name") or "").strip()
        category = next((key for key in POI_KEYS if tags.get(key)), None)
        if name and category:
            if element.get("type") == "node" and "lat" in element and "lon" in element:
                lat, lon = float(element["lat"]), float(element["lon"])
            else:
                centre = element.get("center") or {}
                if "lat" not in centre or "lon" not in centre:
                    continue
                lat, lon = float(centre["lat"]), float(centre["lon"])
            if inside_boundary(lat, lon):
                pois.append(
                    {
                        "id": f"osm_{element.get('type')}_{element.get('id')}",
                        "name": name,
                        "category": category,
                        "subcategory": tags.get(category),
                        "lat": lat,
                        "lng": lon,
                    }
                )

    used_nodes = {edge["from"] for edge in edges} | {edge["to"] for edge in edges}
    nodes = {node_id: nodes[node_id] for node_id in sorted(used_nodes)}
    edges.sort(key=lambda edge: edge["id"])
    pois = sorted({poi["id"]: poi for poi in pois}.values(), key=lambda poi: poi["id"])
    graph: dict[str, Any] = {
        "metadata": {
            "graph_id": "op1-osm-pedestrian-v1",
            "graph_version": "2.0.0",
            "source": "openstreetmap_snapshot",
            "snapshot_at": snapshot_at,
            "license": "Open Database License (ODbL)",
            "attribution": "© OpenStreetMap contributors",
            "overpass_endpoint": OVERPASS_URL,
            "overpass_query_sha256": hashlib.sha256(query_text().encode("utf-8")).hexdigest(),
            "node_count": len(nodes),
            "edge_count": len(edges),
            "poi_count": len(pois),
            "extent": {
                "south": min(point[0] for point in BOUNDARY),
                "west": min(point[1] for point in BOUNDARY),
                "north": max(point[0] for point in BOUNDARY),
                "east": max(point[1] for point in BOUNDARY),
            },
            "boundary": [*BOUNDARY, BOUNDARY[0]],
            "checksum_sha256": "",
        },
        "station_coordinates": STATIONS,
        "nodes": nodes,
        "edges": edges,
        "pois": pois,
        "circuits": {},
    }
    canonical = json.loads(json.dumps(graph))
    canonical["metadata"].pop("checksum_sha256", None)
    encoded = json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    graph["metadata"]["checksum_sha256"] = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
    return graph


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, help="Use a previously downloaded Overpass JSON response")
    parser.add_argument("--raw-output", type=Path, help="Optionally preserve the fetched raw response")
    parser.add_argument("--output", type=Path, default=Path("data/ocean-park-1-pedestrian-graph.json"))
    args = parser.parse_args()
    if args.input:
        raw = json.loads(args.input.read_text(encoding="utf-8"))
        snapshot_at = str((raw.get("osm3s") or {}).get("timestamp_osm_base") or datetime.now(UTC).isoformat())
    else:
        raw = fetch_overpass()
        snapshot_at = str((raw.get("osm3s") or {}).get("timestamp_osm_base") or datetime.now(UTC).isoformat())
        if args.raw_output:
            args.raw_output.parent.mkdir(parents=True, exist_ok=True)
            args.raw_output.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
    graph = build_graph(raw, snapshot_at)
    if len(graph["nodes"]) < 100 or len(graph["edges"]) < 100:
        raise SystemExit("Refusing to write an unexpectedly small pedestrian graph")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(graph, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {len(graph['nodes'])} nodes, {len(graph['edges'])} edges, {len(graph['pois'])} POIs")


if __name__ == "__main__":
    main()
