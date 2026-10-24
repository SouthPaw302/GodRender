#!/usr/bin/env python3
"""Deterministic synthetic geography derived from an authenticated AE scene contract.

Independent implementation of procedural terrain, talus relaxation, D8 drainage,
settlement suitability and slope-aware road routing. No World Gacha source/assets,
ML inference, private media, factual geography or canon promotion.
"""
from __future__ import annotations
import argparse
import hashlib
import heapq
import json
import math
import random
from pathlib import Path
from export_godot_scene import digest

SCHEMA = "american-empire.procedural-geometry.v1"
SIZE = 64
SPAN_M = 2400
SEA = 32.0
OFFSETS = ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1))


def stage_seed(seed: str, stage: str, variation: int = 0) -> int:
    return int.from_bytes(hashlib.sha256(f"{seed}:{stage}:{variation}".encode()).digest()[:8], "little")


def value_noise(n: int, period: int, rng: random.Random) -> list[list[float]]:
    count = math.ceil((n - 1) / period) + 2
    lattice = [[rng.uniform(-1, 1) for _ in range(count)] for _ in range(count)]
    values = [[0.0] * n for _ in range(n)]
    for r in range(n):
        y, fy = divmod(r, period)
        ty = (fy / period) ** 2 * (3 - 2 * (fy / period))
        for c in range(n):
            x, fx = divmod(c, period)
            tx = (fx / period) ** 2 * (3 - 2 * (fx / period))
            a = lattice[y][x] * (1 - tx) + lattice[y][x + 1] * tx
            b = lattice[y + 1][x] * (1 - tx) + lattice[y + 1][x + 1] * tx
            values[r][c] = a * (1 - ty) + b * ty
    return values


def landscape(seed: str, n: int = SIZE) -> list[list[float]]:
    rng = random.Random(stage_seed(seed, "topography"))
    detail = [(amplitude, value_noise(n, period, rng)) for amplitude, period in
              ((18, 24), (9, 12), (4, 6), (1.7, 3))]
    h = []
    for r in range(n):
        row = []
        y = r / (n - 1)
        for c in range(n):
            x = c / (n - 1)
            coastline = .20 + .055 * math.sin(7 * y + .6) + .018 * math.sin(17 * y)
            highland = 65 * math.exp(-(((x - .78) / .23) ** 2 + ((y - .28) / .26) ** 2) / 2)
            valley = 28 * math.exp(-((y - (.59 + .10 * math.sin(5 * x))) / .065) ** 2)
            z = SEA + 105 * (x - coastline) + highland - valley
            z += sum(a * field[r][c] for a, field in detail)
            row.append(max(0.0, z))
        h.append(row)
    return h


def erode(h: list[list[float]], seed: str, rounds: int = 7) -> list[list[float]]:
    n = len(h)
    rng = random.Random(stage_seed(seed, "erosion"))
    talus = 1.0 + rng.random() * .25
    for _ in range(rounds):
        transfers = [[0.0] * n for _ in range(n)]
        for r in range(n):
            for c in range(n):
                for dr, dc in ((1, 0), (0, 1)):
                    rr, cc = r + dr, c + dc
                    if rr >= n or cc >= n:
                        continue
                    diff = h[r][c] - h[rr][cc]
                    if abs(diff) <= talus:
                        continue
                    amount = (abs(diff) - talus) * .055
                    sign = 1 if diff > 0 else -1
                    transfers[r][c] -= amount * sign
                    transfers[rr][cc] += amount * sign
        h = [[max(0.0, h[r][c] + transfers[r][c]) for c in range(n)] for r in range(n)]
    return h


def drainage(h: list[list[float]]) -> tuple[list[list[bool]], list[list[bool]]]:
    n = len(h)
    sea = [[h[r][c] <= SEA for c in range(n)] for r in range(n)]
    visited = [[False] * n for _ in range(n)]
    receiver = [[None] * n for _ in range(n)]
    filled = [[max(z, SEA) for z in row] for row in h]
    heap, order = [], []
    for i in range(n):
        for r, c in ((0, i), (n - 1, i), (i, 0), (i, n - 1)):
            if not visited[r][c]:
                visited[r][c] = True
                heapq.heappush(heap, (filled[r][c], r, c))
                order.append((r, c))
    while heap:
        _, r, c = heapq.heappop(heap)
        for dr, dc in OFFSETS:
            rr, cc = r + dr, c + dc
            if not (0 <= rr < n and 0 <= cc < n) or visited[rr][cc]:
                continue
            visited[rr][cc] = True
            filled[rr][cc] = max(filled[rr][cc], filled[r][c] + .001)
            receiver[rr][cc] = (r, c)
            heapq.heappush(heap, (filled[rr][cc], rr, cc))
            order.append((rr, cc))
    flow = [[1] * n for _ in range(n)]
    for r, c in reversed(order):
        target = receiver[r][c]
        if target:
            rr, cc = target
            flow[rr][cc] += flow[r][c]
    river = [[flow[r][c] > 38 and not sea[r][c] and h[r][c] > SEA + 1
              for c in range(n)] for r in range(n)]
    return river, sea


def distances(mask: list[list[bool]]) -> list[list[int]]:
    from collections import deque
    n = len(mask)
    dist = [[2 * n] * n for _ in range(n)]
    q = deque()
    for r in range(n):
        for c in range(n):
            if mask[r][c]:
                dist[r][c] = 0
                q.append((r, c))
    while q:
        r, c = q.popleft()
        for dr, dc in OFFSETS[:4]:
            rr, cc = r + dr, c + dc
            if 0 <= rr < n and 0 <= cc < n and dist[rr][cc] > dist[r][c] + 1:
                dist[rr][cc] = dist[r][c] + 1
                q.append((rr, cc))
    return dist


def slope_at(h: list[list[float]], r: int, c: int) -> float:
    n = len(h)
    x = abs(h[r][min(n - 1, c + 1)] - h[r][max(0, c - 1)]) * .5
    y = abs(h[min(n - 1, r + 1)][c] - h[max(0, r - 1)][c]) * .5
    return math.hypot(x, y)


def settlement_sites(h, river, sea, seed: str, variation: int = 0) -> list[dict]:
    n = len(h)
    coastline = distances(sea)
    freshwater = distances(river)
    rng = random.Random(stage_seed(seed, "settlements", variation))
    candidates = []
    for r in range(2, n - 2):
        for c in range(2, n - 2):
            if sea[r][c] or h[r][c] <= SEA + 3 or coastline[r][c] < 3:
                continue
            s = slope_at(h, r, c)
            if s > 12:
                continue
            score = 3 * math.exp(-((coastline[r][c] - 10) / 10) ** 2)
            score += 3 * math.exp(-((freshwater[r][c] - 5) / 8) ** 2)
            score += 1.5 / (1 + s) + rng.random() * .55
            candidates.append((score, r, c))
    candidates.sort(reverse=True)
    chosen = []
    for _, r, c in candidates:
        if any((r - a["row"]) ** 2 + (c - a["col"]) ** 2 < 12 ** 2 for a in chosen):
            continue
        chosen.append({"id": f"site-{len(chosen) + 1}", "row": r, "col": c,
                       "elevation_dm": round(h[r][c] * 10)})
        if len(chosen) == 5:
            break
    if len(chosen) < 3:
        raise ValueError("Could not place three independent dry settlements")
    return chosen


def road_path(h, sea, river, a, b, seed: str, variation: int = 0) -> list[list[int]]:
    n = len(h)
    rng = random.Random(stage_seed(seed, "roads", variation))
    jitter = [[rng.random() * .55 for _ in range(n)] for _ in range(n)]
    start = (a["row"], a["col"])
    goal = (b["row"], b["col"])
    frontier = [(0.0, start)]
    costs = {start: 0.0}
    parents = {}
    while frontier:
        _, point = heapq.heappop(frontier)
        if point == goal:
            break
        r, c = point
        for dr, dc in OFFSETS:
            rr, cc = r + dr, c + dc
            if not (0 <= rr < n and 0 <= cc < n) or sea[rr][cc]:
                continue
            cost = math.hypot(dr, dc) * (1 + abs(h[r][c] - h[rr][cc]) * .18 +
                                         (2.2 if river[rr][cc] else 0) + jitter[rr][cc])
            nxt = (rr, cc)
            candidate = costs[point] + cost
            if candidate + 1e-9 < costs.get(nxt, float("inf")):
                costs[nxt] = candidate
                parents[nxt] = point
                heuristic = math.hypot(rr - goal[0], cc - goal[1])
                heapq.heappush(frontier, (candidate + heuristic, nxt))
    if goal not in costs:
        raise ValueError("No viable dry road connection")
    path = [goal]
    while path[-1] != start:
        path.append(parents[path[-1]])
    return [[r, c] for r, c in reversed(path)]


def connect(h, sea, river, sites, seed: str, variation: int = 0) -> list[dict]:
    connected = {0}
    pending = set(range(1, len(sites)))
    roads = []
    while pending:
        i, j = min(((a, b) for a in connected for b in pending),
                   key=lambda ab: ((sites[ab[0]]["row"] - sites[ab[1]]["row"]) ** 2 +
                                   (sites[ab[0]]["col"] - sites[ab[1]]["col"]) ** 2, ab))
        roads.append({"from": sites[i]["id"], "to": sites[j]["id"],
                      "cells": road_path(h, sea, river, sites[i], sites[j], seed, variation)})
        connected.add(j)
        pending.remove(j)
    return roads


def validate_contract(contract: dict) -> None:
    if contract.get("schema") != "american-empire.godot-scene-contract.v1":
        raise ValueError("Only verified P9 scene contracts are accepted")
    if contract.get("authority_layer") != "scenario_only":
        raise ValueError("Unapproved source authority")
    if contract.get("production", {}).get("media_refs_embedded") is not False:
        raise ValueError("Embedded media prohibited")
    signature = contract.get("contract_sha256")
    if not isinstance(signature, str) or signature != digest({k: v for k, v in contract.items() if k != "contract_sha256"}):
        raise ValueError("Scene contract integrity failure")
    source = contract.get("source", {}).get("p7_snapshot_sha256", "")
    if not isinstance(source, str) or len(source) != 64 or any(c not in "0123456789abcdef" for c in source):
        raise ValueError("Missing P7 source snapshot")


def build(contract: dict, *, town_variation: int = 0, road_variation: int = 0) -> dict:
    validate_contract(contract)
    if town_variation < 0 or road_variation < 0 or town_variation > 1000 or road_variation > 1000:
        raise ValueError("Variation outside test bound")
    seed = contract["source"]["p7_snapshot_sha256"] + ":" + contract["world"]["place_id"]
    h = erode(landscape(seed), seed)
    rivers, ocean = drainage(h)
    sites = settlement_sites(h, rivers, ocean, seed, town_variation)
    roads = connect(h, ocean, rivers, sites, seed, road_variation)
    heights = [[round(v * 10) for v in row] for row in h]
    river_cells = [[r, c] for r in range(SIZE) for c in range(SIZE) if rivers[r][c]]
    geometry = {
        "schema": SCHEMA,
        "authority_layer": "scenario_only",
        "real_geography": False,
        "no_private_media": True,
        "source_scene_contract_sha256": contract["contract_sha256"],
        "source_p7_snapshot_sha256": contract["source"]["p7_snapshot_sha256"],
        "place_id": contract["world"]["place_id"],
        "year": contract["world"]["year"],
        "stage_seeds": {
            "landscape": stage_seed(seed, "topography"),
            "erosion": stage_seed(seed, "erosion"),
            "settlements": stage_seed(seed, "settlements", town_variation),
            "roads": stage_seed(seed, "roads", road_variation),
        },
        "extent_m": SPAN_M,
        "grid": SIZE,
        "sea_level_dm": round(SEA * 10),
        "heights_dm": heights,
        "river_cells": river_cells,
        "settlements": sites,
        "roads": roads,
        "terrain_sha256": digest(heights),
        "limitations": "Synthetic regional geography; no real GIS terrain, approved buildings or film media.",
    }
    geometry["geometry_sha256"] = digest(geometry)
    return geometry


def verify_geometry(geometry: dict, contract: dict) -> None:
    validate_contract(contract)
    if geometry.get("schema") != SCHEMA or geometry.get("authority_layer") != "scenario_only":
        raise ValueError("Unknown geometry")
    checksum = geometry.get("geometry_sha256")
    if checksum != digest({k: v for k, v in geometry.items() if k != "geometry_sha256"}):
        raise ValueError("Tampered geometry")
    if geometry.get("source_scene_contract_sha256") != contract["contract_sha256"]:
        raise ValueError("Wrong source contract")
    if geometry.get("source_p7_snapshot_sha256") != contract["source"]["p7_snapshot_sha256"]:
        raise ValueError("Wrong simulation snapshot")
    if geometry.get("place_id") != contract["world"]["place_id"] or geometry.get("year") != contract["world"]["year"]:
        raise ValueError("Wrong simulation place or year")
    if geometry.get("real_geography") is not False or geometry.get("no_private_media") is not True:
        raise ValueError("Geometry provenance invalid")
    heights = geometry.get("heights_dm")
    if geometry.get("grid") != SIZE or not isinstance(heights, list) or len(heights) != SIZE:
        raise ValueError("Wrong grid")
    if any(not isinstance(row, list) or len(row) != SIZE or any(type(v) is not int or v < 0 or v > 65535 for v in row) for row in heights):
        raise ValueError("Malformed heightmap")
    if geometry.get("terrain_sha256") != digest(heights):
        raise ValueError("Terrain hash failure")
    expected = build(contract, town_variation=0, road_variation=0)
    variations = geometry["stage_seeds"]
    # Derived stage variations must be independently reproducible, not client asserted.
    seed = contract["source"]["p7_snapshot_sha256"] + ":" + contract["world"]["place_id"]
    if variations["landscape"] != expected["stage_seeds"]["landscape"] or variations["erosion"] != expected["stage_seeds"]["erosion"]:
        raise ValueError("Wrong physical world")
    if geometry["heights_dm"] != expected["heights_dm"] or geometry["river_cells"] != expected["river_cells"]:
        raise ValueError("Terrain not source-derived")
    if len(geometry.get("settlements", [])) < 3 or len(geometry.get("roads", [])) < 2:
        raise ValueError("Missing settlements or routes")
    for site in geometry["settlements"]:
        if not (0 <= site["row"] < SIZE and 0 <= site["col"] < SIZE):
            raise ValueError("Settlement outside world")
    for road in geometry["roads"]:
        for cell in road["cells"]:
            if not isinstance(cell, list) or len(cell) != 2 or not all(type(v) is int and 0 <= v < SIZE for v in cell):
                raise ValueError("Road outside world")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--contract", type=Path, required=True)
    ap.add_argument("--output", type=Path)
    ap.add_argument("--verify", type=Path)
    ap.add_argument("--town-variation", type=int, default=0)
    ap.add_argument("--road-variation", type=int, default=0)
    opts = ap.parse_args()
    contract = json.loads(opts.contract.read_text(encoding="utf-8"))
    if opts.verify:
        verify_geometry(json.loads(opts.verify.read_text(encoding="utf-8")), contract)
        print("AE_PROCEDURAL_GEOMETRY_VERIFY_PASS")
    else:
        if opts.output is None:
            ap.error("--output is required unless --verify is set")
        geom = build(contract, town_variation=opts.town_variation, road_variation=opts.road_variation)
        opts.output.parent.mkdir(parents=True, exist_ok=True)
        opts.output.write_text(json.dumps(geom, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
        print(f"AE_PROCEDURAL_GEOMETRY_PASS hash={geom['geometry_sha256']} towns={len(geom['settlements'])} roads={len(geom['roads'])}")


if __name__ == "__main__":
    main()
