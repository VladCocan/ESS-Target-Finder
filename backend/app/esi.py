import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any

import httpx

BASE_URL = "https://esi.evetech.net/latest/universe"
SYSTEM_KILLS_PATH = "/system_kills/"
SYSTEM_JUMPS_PATH = "/system_jumps/"
SYSTEM_NAMES_PATH = "/names/"
CACHE_TTL = timedelta(minutes=10)
MAX_RETRIES = 3
TIMEOUT_SECONDS = 10.0
BACKOFF_SECONDS = 1.0

logger = logging.getLogger("backend.app.esi")

_kills_cache: dict[str, tuple[datetime, list[dict[str, Any]]]] = {
    "system_kills": (datetime.min, []),
    "system_jumps": (datetime.min, []),
}
_names_cache: dict[int, tuple[datetime, str]] = {}


async def fetch_json(path: str) -> list[dict[str, Any]]:
    now = datetime.utcnow()
    cache_key = "system_kills" if path == SYSTEM_KILLS_PATH else "system_jumps"
    expires_at, payload = _kills_cache[cache_key]
    if now < expires_at:
        return payload

    url = f"{BASE_URL}{path}"
    timeout = httpx.Timeout(TIMEOUT_SECONDS)

    async with httpx.AsyncClient(timeout=timeout) as client:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
                _kills_cache[cache_key] = (datetime.utcnow() + CACHE_TTL, data)
                return data
            except (httpx.TimeoutException, httpx.HTTPError) as exc:
                logger.warning("ESI request failed (%s) attempt %d/%d: %s", url, attempt, MAX_RETRIES, exc)
                if attempt == MAX_RETRIES:
                    logger.error("ESI fetch failed after %d attempts: %s", MAX_RETRIES, url)
                    return payload
                await asyncio.sleep(BACKOFF_SECONDS)
    return payload


async def post_json(path: str, payload: list[int], params: dict[str, str] | None = None) -> list[dict[str, Any]]:
    url = f"{BASE_URL}{path}"
    timeout = httpx.Timeout(TIMEOUT_SECONDS)

    async with httpx.AsyncClient(timeout=timeout) as client:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = await client.post(url, params=params, json=payload)
                response.raise_for_status()
                return response.json()
            except (httpx.TimeoutException, httpx.HTTPError) as exc:
                logger.warning("ESI POST request failed (%s) attempt %d/%d: %s", url, attempt, MAX_RETRIES, exc)
                if attempt == MAX_RETRIES:
                    logger.error("ESI POST fetch failed after %d attempts: %s", MAX_RETRIES, url)
                    return []
                await asyncio.sleep(BACKOFF_SECONDS)
    return []


async def get_system_kills() -> list[dict[str, Any]]:
    return await fetch_json(SYSTEM_KILLS_PATH)


async def get_system_jumps() -> list[dict[str, Any]]:
    return await fetch_json(SYSTEM_JUMPS_PATH)


async def get_system_names(system_ids: list[int]) -> list[dict[str, Any]]:
    if not system_ids:
        return []

    now = datetime.utcnow()
    params = {"datasource": "tranquility"}
    missing_ids: list[int] = []
    result_map: dict[int, str] = {}

    for system_id in system_ids:
        cache_entry = _names_cache.get(system_id)
        if cache_entry and cache_entry[0] > now:
            result_map[system_id] = cache_entry[1]
        else:
            missing_ids.append(system_id)

    if missing_ids:
        unique_missing = list(dict.fromkeys(missing_ids))
        batch_size = 300
        for start in range(0, len(unique_missing), batch_size):
            batch = unique_missing[start : start + batch_size]
            batch_result = await post_json(SYSTEM_NAMES_PATH, batch, params=params)
            for entry in batch_result:
                system_id = int(entry.get("id", 0))
                name = entry.get("name", "Unknown")
                if system_id:
                    result_map[system_id] = name
                    _names_cache[system_id] = (datetime.utcnow() + CACHE_TTL, name)

        for system_id in unique_missing:
            if system_id not in result_map:
                _names_cache[system_id] = (datetime.utcnow() + CACHE_TTL, "Unknown")
                result_map[system_id] = "Unknown"

    return [{"id": system_id, "name": result_map.get(system_id, "Unknown")} for system_id in system_ids]
