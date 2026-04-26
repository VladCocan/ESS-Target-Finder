from __future__ import annotations

from typing import Iterable

from .models import SystemStats

NPC_WEIGHT = 3.0
EFFICIENCY_WEIGHT = 25.0
JUMP_PENALTY = 3.0
SHIP_PENALTY = 20.0
POD_PENALTY = 30.0


def calculate_score(system: SystemStats) -> float:
    efficiency = system.npc_kills / max(system.jumps, 1)
    return (
        system.npc_kills * NPC_WEIGHT
        + efficiency * EFFICIENCY_WEIGHT
        - system.jumps * JUMP_PENALTY
        - system.ship_kills * SHIP_PENALTY
        - system.pod_kills * POD_PENALTY
    )


def build_system_stats(
    kills: Iterable[dict[str, int]],
    jumps: Iterable[dict[str, int]],
) -> list[SystemStats]:
    merged: dict[int, dict[str, int]] = {}

    for entry in kills:
        system_id = int(entry.get("system_id", 0))
        if system_id == 0:
            continue
        merged.setdefault(system_id, {})
        merged[system_id]["ship_kills"] = int(entry.get("ship_kills", 0))
        merged[system_id]["pod_kills"] = int(entry.get("pod_kills", 0))
        merged[system_id]["npc_kills"] = int(entry.get("npc_kills", 0))

    for entry in jumps:
        system_id = int(entry.get("system_id", 0))
        if system_id == 0:
            continue
        merged.setdefault(system_id, {})
        merged[system_id]["jumps"] = int(entry.get("ship_jumps", 0))

    results: list[SystemStats] = []
    for system_id, values in merged.items():
        npc_kills = values.get("npc_kills", 0)
        if npc_kills == 0:
            continue

        stats = SystemStats(
            system_id=system_id,
            system_name="",
            ship_kills=values.get("ship_kills", 0),
            pod_kills=values.get("pod_kills", 0),
            npc_kills=npc_kills,
            jumps=values.get("jumps", 0),
            score=0.0,
        )
        stats.score = calculate_score(stats)
        if (
            stats.npc_kills < 500
            or stats.jumps > 60
            or stats.ship_kills > 2
            or stats.pod_kills > 1
        ):
            continue
        results.append(stats)

    return sorted(results, key=lambda item: item.score, reverse=True)

