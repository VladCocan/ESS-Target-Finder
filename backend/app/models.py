from pydantic import BaseModel
from typing import Any


class SystemStats(BaseModel):
    system_id: int
    system_name: str
    region_id: int | None = None
    region_name: str | None = None
    constellation_id: int | None = None
    constellation_name: str | None = None
    ship_kills: int
    pod_kills: int
    npc_kills: int
    jumps: int
    score: float
    distance: int = 0


class WalletJournalEntry(BaseModel):
    date: str | None = None
    amount: float | None = None
    balance: float | None = None
    ref_type: str | None = None
    reason: str | None = None


class WalletTransaction(BaseModel):
    date: str | None = None
    amount: float | None = None
    type_id: int | None = None
    type_name: str | None = None
    journal_ref_id: int | None = None


class SkillEntry(BaseModel):
    type_id: int
    type_name: str | None = None
    skillpoints: int
    level: int
    trained_skill_level: int | None = None
    group_id: int | None = None
    group_name: str | None = None


class SkillQueueEntry(BaseModel):
    queue_position: int
    type_id: int
    type_name: str | None = None
    finish_date: str | None = None
    finish_date_localized: str | None = None
    finished_level: int | None = None
    level: int | None = None


class AssetEntry(BaseModel):
    type_id: int
    type_name: str | None = None
    location_id: int | None = None
    location_name: str | None = None
    quantity: int | None = None
    is_singleton: bool | None = None
    flag: int | None = None


class ShipFitItem(BaseModel):
    type_id: int
    type_name: str | None = None
    quantity: int | None = None
    location_flag: str | None = None


class ShipFit(BaseModel):
    high_slots: list[ShipFitItem] = []
    mid_slots: list[ShipFitItem] = []
    low_slots: list[ShipFitItem] = []
    rig_slots: list[ShipFitItem] = []
    subsystem_slots: list[ShipFitItem] = []
    drones: list[ShipFitItem] = []
    cargo: list[ShipFitItem] = []
    other: list[ShipFitItem] = []


class CurrentShipFitResponse(BaseModel):
    ship: dict[str, Any]
    fit: ShipFit
    missing_scope: bool = False


class CharacterProfile(BaseModel):
    character_id: int
    name: str
    corporation_name: str | None = None
    alliance_name: str | None = None
    birthday: str | None = None
    security_status: float | None = None
    portrait_url: str | None = None
    isk_balance: float | None = None
    plex_count: int | None = None
    wallet_journal: list[WalletJournalEntry] | None = None
    wallet_transactions: list[WalletTransaction] | None = None
    total_skill_points: int | None = None
    unallocated_skill_points: int | None = None
    skills: list[SkillEntry] | None = None
    skill_queue: list[SkillQueueEntry] | None = None
    location_name: str | None = None
    location_system_id: int | None = None
    location_station_id: int | None = None
    location_structure_id: int | None = None
    location_station_name: str | None = None
    location_structure_name: str | None = None
    ship_type_id: int | None = None
    ship_type_name: str | None = None
    ship_name: str | None = None
    online_status: bool | None = None
    online_last_login: str | None = None
    online_last_logout: str | None = None
    online_logins: int | None = None
    assets: list[AssetEntry] | None = None
    missing_scopes: list[str] = []
    scopes: str | None = None

