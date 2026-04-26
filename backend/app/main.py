from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .db import get_system_metadata, init_db
from .esi import (
    get_route_distance,
    get_system_ids,
    get_system_info,
    get_system_jumps,
    get_system_kills,
    get_system_names,
    preload_system_metadata,
)
from .models import SystemStats
from .scoring import build_system_stats

CACHE_TTL = timedelta(minutes=10)
MAX_NULLSEC_CANDIDATES = 200

logger = logging.getLogger("app")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

app = FastAPI(title="ESS Target Finder")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup() -> None:
    init_db()
    await preload_system_metadata()


_cache: dict[str, tuple[datetime, list[SystemStats]]] = {}
_cache_lock = asyncio.Lock()


async def filter_nullsec_systems(systems: list[SystemStats]) -> list[SystemStats]:
    if not systems:
        return []

    infos = await asyncio.gather(
        *(get_system_info(system.system_id) for system in systems),
        return_exceptions=True,
    )

    filtered: list[SystemStats] = []
    for system, info in zip(systems, infos):
        if isinstance(info, Exception):
            continue

        security = info.get("security_status")
        if isinstance(security, (float, int)) and security < 0.0:
            system.system_name = info.get("system_name") or system.system_name
            system.constellation_id = info.get("constellation_id")
            system.constellation_name = info.get("constellation_name")
            system.region_id = info.get("region_id")
            system.region_name = info.get("region_name")
            filtered.append(system)

    logger.info("Filtered %d null-sec systems from %d candidates", len(filtered), len(systems))
    return filtered


async def fetch_targets(from_system: str | None = None) -> list[SystemStats]:
    cache_key = from_system or ""
    now = datetime.utcnow()

    async with _cache_lock:
        cache_entry = _cache.get(cache_key)
        if cache_entry and now < cache_entry[0]:
            logger.info("Serving cached target list for %s", cache_key)
            return cache_entry[1]

    kills_data, jumps_data = await asyncio.gather(get_system_kills(), get_system_jumps())

    systems = build_system_stats(kills_data, jumps_data)
    systems = await filter_nullsec_systems(systems)

    if systems:
        for system in systems:
            metadata = get_system_metadata(system.system_id)
            if metadata is not None:
                system.system_name = metadata.get("system_name") or system.system_name
                system.constellation_id = metadata.get("constellation_id")
                system.constellation_name = metadata.get("constellation_name")
                system.region_id = metadata.get("region_id")
                system.region_name = metadata.get("region_name")

        missing_names = [system.system_id for system in systems if not system.system_name]
        if missing_names:
            names_data = await get_system_names(missing_names)
            name_map = {
                int(entry.get("id", 0)): entry.get("name", "Unknown")
                for entry in names_data
                if isinstance(entry.get("id"), int)
            }
            for system in systems:
                if not system.system_name:
                    system.system_name = name_map.get(system.system_id, "Unknown")

        if from_system:
            names_map = await get_system_ids([from_system])
            source_id = names_map.get(from_system)
            if source_id:
                distances = await asyncio.gather(
                    *(get_route_distance(source_id, system.system_id) for system in systems),
                    return_exceptions=True,
                )
                for system, distance in zip(systems, distances):
                    if isinstance(distance, Exception):
                        distance = 0
                    system.distance = distance
                    system.score -= distance * 50
            else:
                logger.warning("Could not resolve from_system '%s' to a system ID", from_system)

    systems.sort(key=lambda item: item.score, reverse=True)

    async with _cache_lock:
        _cache[cache_key] = (datetime.utcnow() + CACHE_TTL, systems)

    logger.info("Fetched and scored %d systems", len(systems))
    return systems


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/targets", response_model=list[SystemStats])
async def targets(
    limit: int = Query(20, ge=1, le=200),
    from_system: str | None = Query(None, alias="from_system", min_length=1),
) -> list[SystemStats]:
    try:
        systems = await fetch_targets(from_system=from_system)
    except Exception as exc:
        logger.exception("Failed to retrieve targets")
        raise HTTPException(status_code=502, detail="Unable to retrieve target systems") from exc

    return systems[:limit]

