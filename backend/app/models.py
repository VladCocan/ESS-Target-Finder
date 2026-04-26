from pydantic import BaseModel


class SystemStats(BaseModel):
    system_id: int
    system_name: str
    ship_kills: int
    pod_kills: int
    npc_kills: int
    jumps: int
    score: float
