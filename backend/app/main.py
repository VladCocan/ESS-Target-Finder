from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .esi import get_system_jumps, get_system_kills, get_system_names
from .models import SystemStats
from .scoring import build_system_stats

CACHE_TTL = timedelta(minutes=10)

logger = logging.getLogger("backend.app")
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


async def fetch_targets() -> list[SystemStats]:
    if datetime.utcnow() < _cache["expires_at"]:
        logger.info("Serving cached target list")
        return _cache["payload"]

    kills_task = get_system_kills()
    jumps_task = get_system_jumps()
    kills_data, jumps_data = await kills_task, await jumps_task

    systems = build_system_stats(kills_data, jumps_data)
    name_map = {}
    if systems:
        system_ids = [system.system_id for system in systems]
        names_data = await get_system_names(system_ids)
        name_map = {
            int(entry.get("id", 0)): entry.get("name", "Unknown")
            for entry in names_data
            if isinstance(entry.get("id"), int)
        }

    for system in systems:
        system.system_name = name_map.get(system.system_id, "Unknown")

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
        logger.exception("Failed to fetch target systems")
        raise HTTPException(status_code=502, detail="Unable to retrieve target systems") from exc

    return systems[:limit]
