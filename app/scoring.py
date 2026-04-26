from __future__ import annotations

from typing import Iterable

from .models import SystemStats


def calculate_score(system: SystemStats) -> float:
    return (
        system.npc_kills * 3.0
        - system.jumps * 1.5
        - system.ship_kills * 8.0
        - system.pod_kills * 10.0
    )


def build_system_stats(
    kills: Iterable[dict[str, int]],
    jumps: Iterable[dict[str, int]],
) -> list[SystemStats]:
    merged: dict[int, dict[str, int]] = {}

    for entry in kills:
        system_id = int(entry.get("system_id", 0))
        merged.setdefault(system_id, {})
        merged[system_id]["ship_kills"] = int(entry.get("ship_kills", 0))
        merged[system_id]["pod_kills"] = int(entry.get("pod_kills", 0))
        merged[system_id]["npc_kills"] = int(entry.get("npc_kills", 0))

    for entry in jumps:
        system_id = int(entry.get("system_id", 0))
        merged.setdefault(system_id, {})
        merged[system_id]["jumps"] = int(entry.get("ship_jumps", 0))

    results: list[SystemStats] = []
    for system_id, values in merged.items():
        npc_kills = values.get("npc_kills", 0)
        if npc_kills == 0:
            continue

        stats = SystemStats(
            system_id=system_id,
            ship_kills=values.get("ship_kills", 0),
            pod_kills=values.get("pod_kills", 0),
            npc_kills=npc_kills,
            jumps=values.get("jumps", 0),
            score=0.0,
        )
        stats.score = calculate_score(stats)
        results.append(stats)

    return sorted(results, key=lambda item: item.score, reverse=True)
