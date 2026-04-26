import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any

import httpx

BASE_URL = "https://esi.evetech.net/latest/universe"
SYSTEM_KILLS_PATH = "/system_kills/"
SYSTEM_JUMPS_PATH = "/system_jumps/"
MAX_RETRIES = 3
TIMEOUT_SECONDS = 10.0
BACKOFF_SECONDS = 1.0

logger = logging.getLogger("app.esi")


def _compute_backoff(attempt: int) -> float:
    return BACKOFF_SECONDS * (2 ** (attempt - 1))


async def fetch_json(path: str) -> list[dict[str, Any]]:
    url = f"{BASE_URL}{path}"
    timeout = httpx.Timeout(TIMEOUT_SECONDS)

    async with httpx.AsyncClient(timeout=timeout) as client:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
            except (httpx.TimeoutException, httpx.HTTPError) as exc:
                logger.warning("ESI request failed (%s) attempt %d/%d: %s", url, attempt, MAX_RETRIES, exc)
                if attempt == MAX_RETRIES:
                    logger.error("ESI fetch failed after %d attempts: %s", MAX_RETRIES, url)
                    return []
                await asyncio.sleep(_compute_backoff(attempt))

    return []


async def get_system_kills() -> list[dict[str, Any]]:
    return await fetch_json(SYSTEM_KILLS_PATH)


async def get_system_jumps() -> list[dict[str, Any]]:
    return await fetch_json(SYSTEM_JUMPS_PATH)

