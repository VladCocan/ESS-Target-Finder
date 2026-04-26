import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any

import httpx

from urllib.parse import quote

BASE_URL = "https://esi.evetech.net/latest/universe"
ROUTE_BASE = "https://esi.evetech.net/latest/route"
SYSTEM_KILLS_PATH = "/system_kills/"
SYSTEM_JUMPS_PATH = "/system_jumps/"
SYSTEM_NAMES_PATH = "/names/"
SYSTEM_IDS_PATH = "/ids/"
SYSTEM_INFO_PATH = "/systems/{system_id}/"
CACHE_TTL = timedelta(minutes=10)
MAX_RETRIES = 3
BACKOFF_BASE = 1.0
MAX_INFO_CONCURRENCY = 10
TIMEOUT = httpx.Timeout(10.0, connect=5.0, read=10.0, write=5.0, pool=5.0)

logger = logging.getLogger("app.esi")

_kills_cache: dict[str, tuple[datetime, list[dict[str, Any]]]] = {
    "system_kills": (datetime.min, []),
    "system_jumps": (datetime.min, []),
}
_names_cache: dict[int, tuple[datetime, str]] = {}
_system_info_cache: dict[int, tuple[datetime, dict[str, Any]]] = {}
_route_cache: dict[tuple[str, str], tuple[datetime, int]] = {}
_cache_lock = asyncio.Lock()
_names_cache_lock = asyncio.Lock()
_info_cache_lock = asyncio.Lock()
_route_cache_lock = asyncio.Lock()
_info_semaphore = asyncio.Semaphore(MAX_INFO_CONCURRENCY)


def _compute_backoff(attempt: int) -> float:
    return BACKOFF_BASE * (2 ** (attempt - 1))


async def fetch_json(path: str) -> list[dict[str, Any]]:
    cache_key = "system_kills" if path == SYSTEM_KILLS_PATH else "system_jumps"
    now = datetime.utcnow()

    async with _cache_lock:
        expires_at, payload = _kills_cache[cache_key]
        if now < expires_at:
            logger.info("Cache hit for %s", cache_key)
            return payload

    url = f"{BASE_URL}{path}"
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
                async with _cache_lock:
                    _kills_cache[cache_key] = (datetime.utcnow() + CACHE_TTL, data)
                logger.info("Fetched %s from ESI (%d records)", cache_key, len(data) if isinstance(data, list) else 0)
                return data
            except (httpx.TimeoutException, httpx.HTTPError) as exc:
                logger.warning("ESI request failed (%s) attempt %d/%d: %s", url, attempt, MAX_RETRIES, exc)
                if attempt == MAX_RETRIES:
                    logger.error("ESI fetch failed after %d attempts: %s", MAX_RETRIES, url)
                    return payload
                await asyncio.sleep(_compute_backoff(attempt))

    return payload


async def post_json(path: str, payload: list[Any], params: dict[str, str] | None = None) -> list[dict[str, Any]]:
    url = f"{BASE_URL}{path}"
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = await client.post(url, params=params, json=payload)
                response.raise_for_status()
                data = response.json()
                logger.info("Fetched %s from ESI (%d records)", path, len(data) if isinstance(data, list) else 0)
                return data
            except (httpx.TimeoutException, httpx.HTTPError) as exc:
                logger.warning("ESI POST request failed (%s) attempt %d/%d: %s", url, attempt, MAX_RETRIES, exc)
                if attempt == MAX_RETRIES:
                    logger.error("ESI POST fetch failed after %d attempts: %s", MAX_RETRIES, url)
                    return []
                await asyncio.sleep(_compute_backoff(attempt))

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
    result_map: dict[int, str] = {}
    missing_ids: list[int] = []

    async with _names_cache_lock:
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
                    async with _names_cache_lock:
                        _names_cache[system_id] = (datetime.utcnow() + CACHE_TTL, name)

        for system_id in unique_missing:
            if system_id not in result_map:
                async with _names_cache_lock:
                    _names_cache[system_id] = (datetime.utcnow() + CACHE_TTL, "Unknown")
                result_map[system_id] = "Unknown"

    return [{"id": system_id, "name": result_map.get(system_id, "Unknown")} for system_id in system_ids]


async def get_system_ids(system_names: list[str]) -> dict[str, int]:
    if not system_names:
        return {}

    params = {"datasource": "tranquility"}
    result_map: dict[str, int] = {}
    batch_result = await post_json(SYSTEM_IDS_PATH, system_names, params=params)
    if isinstance(batch_result, dict):
        system_entries = batch_result.get("systems", [])
        for entry in system_entries:
            system_id = int(entry.get("id", 0))
            name = entry.get("name")
            if name and system_id:
                result_map[name] = system_id
    return result_map


async def get_route_distance(from_id: int, to_id: int) -> int:
    if from_id <= 0 or to_id <= 0:
        return 0

    key = (str(from_id), str(to_id))
    now = datetime.utcnow()
    async with _route_cache_lock:
        cache_entry = _route_cache.get(key)
        if cache_entry and cache_entry[0] > now:
            return cache_entry[1]

    path = f"{ROUTE_BASE}/{from_id}/{to_id}/"
    params = {"datasource": "tranquility"}
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = await client.get(path, params=params)
                response.raise_for_status()
                data = response.json()
                if isinstance(data, list):
                    distance = max(0, len(data) - 1)
                else:
                    distance = 0
                async with _route_cache_lock:
                    _route_cache[key] = (datetime.utcnow() + CACHE_TTL, distance)
                return distance
            except (httpx.TimeoutException, httpx.HTTPError) as exc:
                logger.warning("ESI route request failed (%s) attempt %d/%d: %s", path, attempt, MAX_RETRIES, exc)
                if attempt == MAX_RETRIES:
                    logger.error("ESI route fetch failed after %d attempts: %s", MAX_RETRIES, path)
                    return 0
                await asyncio.sleep(_compute_backoff(attempt))

    return 0


async def get_system_info(system_id: int) -> dict[str, Any]:
    now = datetime.utcnow()
    async with _info_cache_lock:
        cache_entry = _system_info_cache.get(system_id)
        if cache_entry and cache_entry[0] > now:
            return cache_entry[1]

    url = f"{BASE_URL}{SYSTEM_INFO_PATH.format(system_id=system_id)}"
    params = {"datasource": "tranquility"}

    async with _info_semaphore:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            for attempt in range(1, MAX_RETRIES + 1):
                try:
                    response = await client.get(url, params=params)
                    response.raise_for_status()
                    data = response.json()
                    async with _info_cache_lock:
                        _system_info_cache[system_id] = (datetime.utcnow() + CACHE_TTL, data)
                    return data
                except (httpx.TimeoutException, httpx.HTTPError) as exc:
                    logger.warning("ESI info fetch failed (%s) attempt %d/%d: %s", url, attempt, MAX_RETRIES, exc)
                    if attempt == MAX_RETRIES:
                        logger.error("ESI info fetch failed after %d attempts: %s", MAX_RETRIES, url)
                        return {}
                    await asyncio.sleep(_compute_backoff(attempt))

    return {}

