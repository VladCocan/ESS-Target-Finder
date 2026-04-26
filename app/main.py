from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .esi import get_system_info, get_system_jumps, get_system_kills, get_system_names
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

_cache: dict[str, Any] = {
    "expires_at": datetime.min,
    "payload": [],
}
_cache_lock = asyncio.Lock()


async def filter_nullsec_systems(systems: list[SystemStats]) -> list[SystemStats]:
    if not systems:
        return []

    candidates = systems[:MAX_NULLSEC_CANDIDATES]
    infos = await asyncio.gather(
        *(get_system_info(system.system_id) for system in candidates),
        return_exceptions=True,
    )

    filtered: list[SystemStats] = []
    for system, info in zip(candidates, infos):
        if isinstance(info, Exception):
            continue

        security = info.get("security_status")
        if isinstance(security, (float, int)) and security < 0.0:
            filtered.append(system)

    logger.info("Filtered %d null-sec systems from %d candidates", len(filtered), len(candidates))
    return filtered


async def fetch_targets() -> list[SystemStats]:
    now = datetime.utcnow()
    async with _cache_lock:
        if now < _cache["expires_at"]:
            logger.info("Serving cached target list")
            return _cache["payload"]

    kills_data, jumps_data = await asyncio.gather(get_system_kills(), get_system_jumps())

    systems = build_system_stats(kills_data, jumps_data)
    systems = await filter_nullsec_systems(systems)

    if systems:
        names_data = await get_system_names([system.system_id for system in systems])
        name_map = {
            int(entry.get("id", 0)): entry.get("name", "Unknown")
            for entry in names_data
            if isinstance(entry.get("id"), int)
        }
        for system in systems:
            system.system_name = name_map.get(system.system_id, "Unknown")

    async with _cache_lock:
        _cache["payload"] = systems
        _cache["expires_at"] = datetime.utcnow() + CACHE_TTL

    logger.info("Fetched and scored %d systems", len(systems))
    return systems


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/targets", response_model=list[SystemStats])
async def targets(limit: int = Query(20, ge=1, le=200)) -> list[SystemStats]:
    try:
        systems = await fetch_targets()
    except Exception as exc:
        logger.exception("Failed to retrieve targets")
        raise HTTPException(status_code=502, detail="Unable to retrieve target systems") from exc

    return systems[:limit]
