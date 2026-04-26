from pydantic import BaseModel


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

