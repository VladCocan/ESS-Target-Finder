from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from threading import Thread
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from .auth import (
    router as auth_router,
    get_optional_auth_session,
    _ensure_fresh_token,
    _fetch_location,
    _get_auth_session_or_401,
)
from .db import get_all_system_metadata_async, get_system_count, init_db
from .esi import (
    get_character_info,
    get_character_location,
    get_character_portrait,
    get_character_ship,
    get_character_wallet_balance,
    get_character_wallet_journal,
    get_character_wallet_transactions,
    get_character_skills,
    get_character_skill_queue,
    get_character_online,
    get_character_assets,
    get_character_assets_all,
    get_corporation_info,
    get_alliance_info,
    get_route_distance,
    get_system_ids,
    get_system_jumps,
    get_system_kills,
    get_type_infos,
    get_group_infos,
    get_category_infos,
    preload_system_metadata,
    resolve_names,
)
from .models import CharacterProfile, CurrentShipFitResponse, SystemStats
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

        metadata = await get_all_system_metadata_async()
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
            scored_candidates: list[SystemStats] = []
            for system, distance in zip(candidates, distances):
                if isinstance(distance, Exception):
                    logger.warning("Route lookup failed for %s: %s", system.system_id, distance)
                    continue
                if distance is None:
                    logger.warning("Route distance unavailable for %s", system.system_id)
                    continue
                system.distance = distance
                system.score = system.score - distance * 75
                scored_candidates.append(system)

            candidates = scored_candidates
            if max_distance is not None:
                candidates = [system for system in candidates if system.distance <= max_distance]

            candidates.sort(key=lambda item: item.score, reverse=True)
            systems = candidates
        else:
            logger.warning("Could not resolve from_system '%s' to a system ID", from_system)
            raise HTTPException(status_code=400, detail=f"Unknown origin system: {from_system}")

    systems.sort(key=lambda item: item.score, reverse=True)

    async with _cache_lock:
        _cache[cache_key] = (datetime.utcnow() + CACHE_TTL, systems)

    logger.info("Fetched and scored %d systems", len(systems))
    return systems


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/character/skills/export")
async def export_character_skills(request: Request) -> PlainTextResponse:
    session = await _get_auth_session_or_401(request)
    session = await _ensure_fresh_token(session)
    access_token = session["access_token"]
    character_id = session["character_id"]
    scopes = session.get("scope", "") or ""
    scope_set = set(scopes.split())
    if "esi-skills.read_skills.v1" not in scope_set:
        raise HTTPException(status_code=403, detail="Missing scope: esi-skills.read_skills.v1")

    skills_data = await get_character_skills(character_id, access_token)
    if not skills_data:
        raise HTTPException(status_code=502, detail="Unable to fetch skills from ESI")

    total_sp = int(skills_data.get("total_sp", 0))
    unallocated_sp = int(skills_data.get("unallocated_sp", 0))
    raw_skills = [
        entry
        for entry in skills_data.get("skills", [])
        if entry.get("skill_id") is not None
    ]
    skill_ids = [int(entry["skill_id"]) for entry in raw_skills if entry.get("skill_id") is not None]
    resolved_names = await resolve_names(list(set(skill_ids))) if skill_ids else {}
    type_infos = await get_type_infos(list(set(skill_ids))) if skill_ids else {}

    group_ids = [info.get("group_id") for info in type_infos.values() if info.get("group_id")]
    group_infos = await get_group_infos(group_ids) if group_ids else {}

    category_ids = [info.get("category_id") for info in group_infos.values() if info.get("category_id")]
    category_infos = await get_category_infos(category_ids) if category_ids else {}

    unique_skills: dict[int, dict[str, Any]] = {}
    for entry in raw_skills:
        skill_id = int(entry.get("skill_id", 0))
        if skill_id <= 0 or skill_id in unique_skills:
            continue

        type_info = type_infos.get(skill_id, {})
        group_id = int(type_info.get("group_id", 0)) if type_info.get("group_id") is not None else None
        group_info = group_infos.get(group_id, {}) if group_id else {}
        category_id = int(group_info.get("category_id", 0)) if group_info.get("category_id") is not None else None
        category_name = category_infos.get(category_id, {}).get("name") if category_id else None
        category_name = category_name or group_info.get("name") or entry.get("group_name") or "Unknown Category"

        skill_name = type_info.get("name") or entry.get("skill_name") or resolved_names.get(skill_id) or f"Unknown Skill (ID: {skill_id})"
        trained_level = entry.get("trained_skill_level")
        if trained_level is None:
            trained_level = entry.get("active_skill_level", 0)
        try:
            trained_level = int(trained_level)
        except (TypeError, ValueError):
            trained_level = 0
        skillpoints = int(entry.get("skillpoints", 0)) if entry.get("skillpoints") is not None else 0

        unique_skills[skill_id] = {
            "skill_name": skill_name,
            "trained_skill_level": trained_level,
            "skillpoints": skillpoints,
            "category_name": category_name,
        }

    grouped_skills: dict[str, list[dict[str, Any]]] = {}
    for skill in unique_skills.values():
        category = skill.get("category_name") or "Unknown Category"
        grouped_skills.setdefault(category, []).append(skill)

    for skills in grouped_skills.values():
        skills.sort(key=lambda item: item["skill_name"].lower())

    sorted_categories = sorted(grouped_skills.keys(), key=lambda name: name.lower())

    lines = [
        "Character Skills",
        "",
        f"Total SP: {total_sp}",
        f"Unallocated SP: {unallocated_sp}",
        "",
    ]
    for category in sorted_categories:
        lines.append(f"=== {category} ===")
        for item in grouped_skills[category]:
            lines.append(f"{item['skill_name']} — Level {item['trained_skill_level']} — {item['skillpoints']} SP")
        lines.append("")

    if lines and lines[-1] == "":
        lines.pop()
    lines.append("--------------------------------")

    export_text = "\n".join(lines)
    return PlainTextResponse(content=export_text, media_type="text/plain")


@app.get("/character/current-ship/fit", response_model=CurrentShipFitResponse)
async def get_current_ship_fit(request: Request) -> CurrentShipFitResponse:
    session = await _get_auth_session_or_401(request)
    session = await _ensure_fresh_token(session)
    access_token = session["access_token"]
    character_id = session["character_id"]
    scopes = session.get("scope", "") or ""
    scope_set = set(scopes.split())
    if "esi-assets.read_assets.v1" not in scope_set:
        raise HTTPException(status_code=403, detail="Missing scope: esi-assets.read_assets.v1")

    ship_data = await get_character_ship(character_id, access_token)
    if not ship_data:
        raise HTTPException(status_code=502, detail="Unable to fetch current ship from ESI")

    ship_item_id = ship_data.get("ship_item_id") or ship_data.get("item_id")
    if not ship_item_id:
        raise HTTPException(status_code=400, detail="Current ship item_id unavailable; cannot resolve fit from assets.")

    try:
        ship_item_id = int(ship_item_id)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="Current ship item_id unavailable; cannot resolve fit from assets.")

    ship_type_id = int(ship_data.get("ship_type_id", 0)) if ship_data.get("ship_type_id") is not None else None
    ship_name = ship_data.get("ship_name")
    ship_type_name = None
    if ship_type_id:
        type_names = await resolve_names([ship_type_id])
        ship_type_name = type_names.get(ship_type_id)

    assets = await get_character_assets_all(character_id, access_token)
    if assets is None:
        raise HTTPException(status_code=502, detail="Unable to fetch character assets from ESI")

    ship_asset = None
    for asset in assets:
        item_id = asset.get("item_id") or asset.get("ship_item_id")
        if item_id is None:
            continue
        try:
            if int(item_id) == ship_item_id:
                ship_asset = asset
                break
        except (TypeError, ValueError):
            continue

    if not ship_asset:
        raise HTTPException(status_code=404, detail="Current ship not found in character assets.")

    fit_items = []
    for asset in assets:
        if asset.get("location_id") is None:
            continue
        try:
            if int(asset.get("location_id")) != ship_item_id:
                continue
        except (TypeError, ValueError):
            continue
        fit_items.append(asset)

    type_ids = [int(item.get("type_id", 0)) for item in fit_items if item.get("type_id") is not None]
    type_names = await resolve_names(list(set(type_ids))) if type_ids else {}

    def flag_category(raw_flag: str | int | None) -> str:
        if raw_flag is None:
            return "other"
        flag_value = str(raw_flag)
        if flag_value.startswith("HiSlot"):
            return "high_slots"
        if flag_value.startswith("MedSlot"):
            return "mid_slots"
        if flag_value.startswith("LoSlot"):
            return "low_slots"
        if flag_value.startswith("RigSlot"):
            return "rig_slots"
        if flag_value.startswith("SubSystemSlot"):
            return "subsystem_slots"
        if "DroneBay" in flag_value:
            return "drones"
        if "Cargo" in flag_value or "Hangar" in flag_value or "Hold" in flag_value:
            return "cargo"
        return "other"

    fit: dict[str, list[dict[str, Any]]] = {
        "high_slots": [],
        "mid_slots": [],
        "low_slots": [],
        "rig_slots": [],
        "subsystem_slots": [],
        "drones": [],
        "cargo": [],
        "other": [],
    }

    for item in fit_items:
        item_type_id = int(item.get("type_id", 0)) if item.get("type_id") is not None else None
        if item_type_id is None:
            continue
        item_type_name = type_names.get(item_type_id)
        quantity = int(item.get("quantity", 0)) if item.get("quantity") is not None else 0
        location_flag = item.get("location_flag") or item.get("flag")
        category_key = flag_category(location_flag)
        fit[category_key].append(
            {
                "type_id": item_type_id,
                "type_name": item_type_name,
                "quantity": quantity,
                "location_flag": str(location_flag) if location_flag is not None else None,
            }
        )

    return CurrentShipFitResponse(
        ship={
            "item_id": ship_item_id,
            "type_id": ship_type_id,
            "type_name": ship_type_name,
            "name": ship_name,
        },
        fit=fit,
        missing_scope=False,
    )


@app.get("/character/profile", response_model=CharacterProfile)
async def current_character_profile(request: Request) -> CharacterProfile:
    return await current_character(request)

@app.get("/character", response_model=CharacterProfile)
async def current_character(request: Request) -> CharacterProfile:
    session = await _get_auth_session_or_401(request)
    session = await _ensure_fresh_token(session)
    access_token = session["access_token"]
    character_id = session["character_id"]
    scopes = session.get("scope", "") or ""
    scope_set = set(scopes.split())

    def missing_scope(required: str) -> bool:
        return required not in scope_set

    missing_scopes: list[str] = []
    if missing_scope("esi-wallet.read_character_wallet.v1"):
        missing_scopes.append("esi-wallet.read_character_wallet.v1")
    if missing_scope("esi-skills.read_skills.v1"):
        missing_scopes.append("esi-skills.read_skills.v1")
    if missing_scope("esi-skills.read_skillqueue.v1"):
        missing_scopes.append("esi-skills.read_skillqueue.v1")
    if missing_scope("esi-location.read_location.v1"):
        missing_scopes.append("esi-location.read_location.v1")
    if missing_scope("esi-location.read_ship_type.v1"):
        missing_scopes.append("esi-location.read_ship_type.v1")
    if missing_scope("esi-location.read_online.v1"):
        missing_scopes.append("esi-location.read_online.v1")
    if missing_scope("esi-assets.read_assets.v1"):
        missing_scopes.append("esi-assets.read_assets.v1")

    character_info = await get_character_info(character_id)
    if not character_info or not character_info.get("name"):
        raise HTTPException(status_code=404, detail="Character not found")

    portrait_url = await get_character_portrait(character_id)
    corp_name = None
    alliance_name = None
    if character_info.get("corporation_id"):
        corp = await get_corporation_info(int(character_info["corporation_id"]))
        corp_name = corp.get("name") if corp else None
    if character_info.get("alliance_id"):
        alli = await get_alliance_info(int(character_info["alliance_id"]))
        alliance_name = alli.get("name") if alli else None

    wallet_balance = None
    wallet_journal = None
    wallet_transactions = None
    if "esi-wallet.read_character_wallet.v1" not in missing_scopes:
        wallet_balance = await get_character_wallet_balance(character_id, access_token)
        wallet_journal = await get_character_wallet_journal(character_id, access_token)
        wallet_transactions = await get_character_wallet_transactions(character_id, access_token)

    skills_data = None
    skill_queue = None
    total_sp = None
    unallocated_sp = None
    skills = None
    if "esi-skills.read_skills.v1" not in missing_scopes:
        skills_data = await get_character_skills(character_id, access_token)
        if isinstance(skills_data, dict):
            total_sp = int(skills_data.get("total_sp", 0))
            unallocated_sp = int(skills_data.get("unallocated_sp", 0))
            skill_ids = [
                int(entry.get("skill_id", 0))
                for entry in skills_data.get("skills", [])
                if entry.get("skill_id") is not None
            ]
            type_infos = await get_type_infos(list(set(skill_ids))) if skill_ids else {}
            group_ids = [info.get("group_id") for info in type_infos.values() if info.get("group_id")]
            group_infos = await get_group_infos(group_ids) if group_ids else {}

            skills = []
            for entry in skills_data.get("skills", []):
                if entry.get("skill_id") is None:
                    continue
                skill_id = int(entry.get("skill_id", 0))
                type_info = type_infos.get(skill_id, {})
                group_id = int(type_info.get("group_id", 0)) if type_info.get("group_id") is not None else None
                group_name = entry.get("group_name")
                if not group_name and group_id:
                    group_name = group_infos.get(group_id, {}).get("name")

                skills.append({
                    "type_id": skill_id,
                    "type_name": entry.get("skill_name") or None,
                    "skillpoints": int(entry.get("skillpoints", 0)),
                    "level": int(entry.get("active_skill_level", 0)),
                    "trained_skill_level": int(entry.get("trained_skill_level", 0)) if entry.get("trained_skill_level") is not None else None,
                    "group_id": group_id,
                    "group_name": group_name,
                })

            missing_skill_ids = [skill["type_id"] for skill in skills if skill["type_id"] and not skill["type_name"]]
            if missing_skill_ids:
                type_map = await resolve_names(list(set(missing_skill_ids)))
                for skill in skills:
                    if skill["type_id"] and not skill["type_name"]:
                        skill["type_name"] = type_map.get(skill["type_id"])
    if "esi-skills.read_skillqueue.v1" not in missing_scopes:
        raw_skill_queue = await get_character_skill_queue(character_id, access_token)
        logger.debug("Raw ESI skill queue for character %s: %s", character_id, raw_skill_queue)
        if isinstance(raw_skill_queue, list):
            def parse_queue_id(entry: dict[str, Any]) -> int:
                for key in ("skill_id", "type_id", "typeID", "skillTypeID"):
                    if entry.get(key) is not None:
                        try:
                            return int(entry[key])
                        except (TypeError, ValueError):
                            continue
                return 0

            def parse_queue_level(entry: dict[str, Any]) -> int | None:
                for key in ("finished_level", "level", "skill_level", "skillLevel"):
                    if entry.get(key) is not None:
                        try:
                            return int(entry[key])
                        except (TypeError, ValueError):
                            continue
                return None

            skill_queue = []
            for index, entry in enumerate(raw_skill_queue):
                queue_id = parse_queue_id(entry)
                if not queue_id:
                    continue

                finished_level = parse_queue_level(entry)
                skill_queue.append(
                    {
                        "queue_position": index + 1,
                        "type_id": queue_id,
                        "type_name": entry.get("skill_name") or entry.get("type_name") or None,
                        "finish_date": entry.get("finish_date"),
                        "finish_date_localized": entry.get("finish_date_localized"),
                        "finished_level": finished_level,
                        "level": finished_level,
                    }
                )

            missing_queue_ids = [item["type_id"] for item in skill_queue if item["type_id"]]
            if missing_queue_ids:
                queue_type_map = await resolve_names(list(set(missing_queue_ids)))
                for item in skill_queue:
                    if item["type_id"] and not item["type_name"]:
                        item["type_name"] = queue_type_map.get(item["type_id"])

    location_name = None
    location_system_id = None
    location_station_id = None
    location_structure_id = None
    location_station_name = None
    location_structure_name = None
    ship_type_id = None
    ship_type_name = None
    ship_name = None
    online_status = None
    online_last_login = None
    online_last_logout = None
    online_logins = None

    if "esi-location.read_location.v1" not in missing_scopes:
        location_data = await get_character_location(character_id, access_token)
        if location_data:
            location_system_id = int(location_data.get("solar_system_id") or location_data.get("system_id") or 0) or None
            location_station_id = int(location_data.get("station_id", 0)) if location_data.get("station_id") is not None else None
            location_structure_id = int(location_data.get("structure_id", 0)) if location_data.get("structure_id") is not None else None

            resolve_ids: list[int] = []
            if location_system_id:
                resolve_ids.append(location_system_id)
            if location_station_id:
                resolve_ids.append(location_station_id)
            if location_structure_id:
                resolve_ids.append(location_structure_id)

            if resolve_ids:
                name_map = await resolve_names(resolve_ids)
                if location_system_id:
                    location_name = name_map.get(location_system_id)
                if location_station_id:
                    location_station_name = name_map.get(location_station_id)
                if location_structure_id:
                    location_structure_name = name_map.get(location_structure_id)

    if "esi-location.read_ship_type.v1" not in missing_scopes:
        ship_data = await get_character_ship(character_id, access_token)
        if ship_data:
            ship_type_id = int(ship_data.get("ship_type_id", 0)) if ship_data.get("ship_type_id") is not None else None
            ship_name = ship_data.get("ship_name")
            if ship_type_id:
                type_map = await resolve_names([ship_type_id])
                ship_type_name = type_map.get(ship_type_id)

    if "esi-location.read_online.v1" not in missing_scopes:
        online_data = await get_character_online(character_id, access_token)
        if online_data:
            online_status = online_data.get("online")
            online_last_login = online_data.get("last_login")
            online_last_logout = online_data.get("last_logout")
            online_logins = int(online_data.get("logins", 0)) if online_data.get("logins") is not None else None

    assets = None
    plex_count = None
    plex_balance = None
    plex_source = None
    plex_error = None
    if "esi-assets.read_assets.v1" not in missing_scopes:
        raw_assets = await get_character_assets_all(character_id, access_token)
        if isinstance(raw_assets, list):
            assets = [
                {
                    "type_id": int(asset.get("type_id", 0)),
                    "type_name": None,
                    "location_id": int(asset.get("location_id", 0)) if asset.get("location_id") is not None else None,
                    "location_name": None,
                    "quantity": int(asset.get("quantity", 0)) if asset.get("quantity") is not None else None,
                    "is_singleton": bool(asset.get("is_singleton", False)),
                    "flag": int(asset.get("flag", 0)) if asset.get("flag") is not None else None,
                }
                for asset in raw_assets
                if asset.get("type_id") is not None
            ]
            item_type_ids = [asset["type_id"] for asset in assets if asset["type_id"]]
            if item_type_ids:
                type_infos = await get_type_infos(item_type_ids)
                for asset in assets:
                    type_info = type_infos.get(asset["type_id"], {})
                    asset["type_name"] = type_info.get("name")
            plex_type_ids = {44992}
            plex_balance = 0
            for asset in assets:
                type_name = asset.get("type_name")
                if asset.get("type_id") in plex_type_ids or (
                    isinstance(type_name, str) and "PLEX" in type_name.upper()
                ):
                    plex_balance += asset.get("quantity", 0) or 0
            plex_count = plex_balance
            plex_source = "assets" if plex_balance > 0 else None
        else:
            plex_error = "Unable to fetch character assets from ESI"
    else:
        plex_error = "Missing scope: esi-assets.read_assets.v1"

    return CharacterProfile(
        character_id=character_id,
        name=str(character_info.get("name", "Unknown")),
        corporation_name=corp_name,
        alliance_name=alliance_name,
        birthday=str(character_info.get("birthday")) if character_info.get("birthday") else None,
        security_status=float(character_info.get("security_status")) if character_info.get("security_status") is not None else None,
        portrait_url=portrait_url,
        isk_balance=wallet_balance,
        plex_count=plex_count,
        plex_balance=plex_balance,
        plex_source=plex_source,
        plex_error=plex_error,
        wallet_journal=[
            {
                "date": entry.get("date"),
                "amount": float(entry.get("amount", 0)),
                "balance": float(entry.get("balance")) if entry.get("balance") is not None else None,
                "ref_type": entry.get("ref_type"),
                "reason": entry.get("reason"),
            }
            for entry in wallet_journal or []
        ] if wallet_journal else None,
        wallet_transactions=[
            {
                "date": entry.get("date"),
                "amount": float(entry.get("amount", 0)),
                "type_id": int(entry.get("type_id", 0)) if entry.get("type_id") is not None else None,
                "type_name": None,
                "journal_ref_id": int(entry.get("journal_ref_id", 0)) if entry.get("journal_ref_id") is not None else None,
            }
            for entry in wallet_transactions or []
        ] if wallet_transactions else None,
        total_skill_points=total_sp,
        unallocated_skill_points=unallocated_sp,
        skills=skills,
        skill_queue=skill_queue if skill_queue else None,
        location_name=location_name,
        location_system_id=location_system_id,
        location_station_id=location_station_id,
        location_structure_id=location_structure_id,
        location_station_name=location_station_name,
        location_structure_name=location_structure_name,
        ship_type_id=ship_type_id,
        ship_type_name=ship_type_name,
        ship_name=ship_name,
        online_status=online_status,
        online_last_login=online_last_login,
        online_last_logout=online_last_logout,
        online_logins=online_logins,
        assets=assets,
        missing_scopes=missing_scopes,
        scopes=scopes,
    )


@app.get("/targets", response_model=list[SystemStats])
async def targets(
    limit: int = Query(20, ge=1, le=200),
    from_system: str = Query("Jita", alias="from_system", min_length=1),
    fromSystem: str | None = Query(None, alias="fromSystem", min_length=1),
    max_distance: int | None = Query(None, alias="max_distance", ge=0),
    maxDistance: int | None = Query(None, alias="maxDistance", ge=0),
) -> list[SystemStats]:
    effective_from_system = fromSystem or from_system
    effective_max_distance = maxDistance if maxDistance is not None else max_distance

    try:
        systems = await fetch_targets(from_system=effective_from_system, max_distance=effective_max_distance)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to retrieve targets")
        raise HTTPException(status_code=502, detail="Unable to retrieve target systems") from exc

    return systems[:limit]

