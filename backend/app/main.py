from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from threading import Thread
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .auth import router as auth_router
from .db import get_all_system_metadata, get_system_count, init_db
from .esi import (
    get_route_distance,
    get_system_ids,
    get_system_jumps,
    get_system_kills,
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
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
app.include_router(auth_router)


def start_metadata_preload() -> None:
    start_time = datetime.utcnow()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(preload_system_metadata())
    finally:
        loop.close()

    final_count = get_system_count()
    elapsed = datetime.utcnow() - start_time
    logger.info("Universe preload complete (final count=%d, time=%s)", final_count, elapsed)


@app.on_event("startup")
async def on_startup() -> None:
    init_db()
    current_count = get_system_count()
    logger.info("Current systems in DB: %d", current_count)
    if current_count <= 5000:
        logger.info("Starting universe preload...")
        thread = Thread(target=start_metadata_preload, daemon=True)
        thread.start()
    else:
        logger.info("Skipping universe preload; DB already has %d systems", current_count)


_cache: dict[str, tuple[datetime, list[SystemStats]]] = {}
_cache_lock = asyncio.Lock()
_metadata_cache: dict[int, dict[str, Any]] = {}
_metadata_cache_timestamp: datetime | None = None
_metadata_cache_lock = asyncio.Lock()
METADATA_CACHE_TTL = timedelta(minutes=5)


async def load_metadata_cache() -> dict[int, dict[str, Any]]:
    global _metadata_cache_timestamp, _metadata_cache
    now = datetime.utcnow()
    async with _metadata_cache_lock:
        if _metadata_cache_timestamp and now - _metadata_cache_timestamp < METADATA_CACHE_TTL:
            return _metadata_cache

        metadata = get_all_system_metadata()
        _metadata_cache = metadata
        _metadata_cache_timestamp = now
        logger.info("Loaded %d system metadata entries from DB", len(metadata))
        return metadata


async def filter_nullsec_systems(systems: list[SystemStats], metadata_map: dict[int, dict[str, Any]]) -> list[SystemStats]:
    if not systems:
        return []

    filtered: list[SystemStats] = []
    missing_ids: list[int] = []
    lookups = 0

    for system in systems:
        lookups += 1
        metadata = metadata_map.get(system.system_id)
        if metadata is None:
            missing_ids.append(system.system_id)
            continue

        security = metadata.get("security_status")
        if isinstance(security, (float, int)) and security < 0.0:
            system.system_name = metadata.get("system_name") or system.system_name
            system.constellation_id = metadata.get("constellation_id")
            system.constellation_name = metadata.get("constellation_name")
            system.region_id = metadata.get("region_id")
            system.region_name = metadata.get("region_name")
            filtered.append(system)

    logger.info("Performed %d metadata lookups, missing %d system IDs", lookups, len(missing_ids))
    if missing_ids:
        logger.warning("Missing system metadata for system IDs: %s", missing_ids)
    logger.info("Filtered %d null-sec systems from %d candidates", len(filtered), len(systems))
    return filtered


async def fetch_targets(from_system: str | None = None, max_distance: int | None = None) -> list[SystemStats]:
    cache_key = f"{from_system or ''}|{max_distance if max_distance is not None else 'none'}"
    now = datetime.utcnow()

    async with _cache_lock:
        cache_entry = _cache.get(cache_key)
        if cache_entry and now < cache_entry[0]:
            logger.info("Serving cached target list for %s", cache_key)
            return cache_entry[1]

    kills_data, jumps_data = await asyncio.gather(get_system_kills(), get_system_jumps())

    systems = build_system_stats(kills_data, jumps_data)
    metadata_map = await load_metadata_cache()
    systems = await filter_nullsec_systems(systems, metadata_map)

    if systems and from_system:
        names_map = await get_system_ids([from_system])
        source_id = names_map.get(from_system)
        if source_id:
            candidates = systems[:MAX_NULLSEC_CANDIDATES]
            distances = await asyncio.gather(
                *(get_route_distance(source_id, system.system_id) for system in candidates),
                return_exceptions=True,
            )
            for system, distance in zip(candidates, distances):
                if isinstance(distance, Exception):
                    distance = 0
                system.distance = distance
                system.score = system.score - distance * 75

            if max_distance is not None:
                candidates = [system for system in candidates if system.distance <= max_distance]

            candidates.sort(key=lambda item: item.score, reverse=True)
            systems = candidates
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
    from_system: str = Query("Jita", alias="from_system", min_length=1),
    max_distance: int | None = Query(None, alias="max_distance", ge=0),
) -> list[SystemStats]:
    try:
        systems = await fetch_targets(from_system=from_system, max_distance=max_distance)
    except Exception as exc:
        logger.exception("Failed to retrieve targets")
        raise HTTPException(status_code=502, detail="Unable to retrieve target systems") from exc

    return systems[:limit]

