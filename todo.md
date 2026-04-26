You are a senior Python backend engineer.

Build a minimal but production-structured FastAPI application called **ESS-Target-Finder** that runs ONLY in Docker (no virtual environments).

## GOAL

Create a service that identifies the best null-sec systems in EVE Online for ESS robbery using ESI public data.

The app must:

* Fetch ESI data
* Compute a score per system
* Return top candidate systems via API

---

## TECH STACK

* Python 3.12
* FastAPI
* Uvicorn
* httpx (async HTTP)
* Docker only (no venv)
* Simple JSON or in-memory cache

---

## PROJECT STRUCTURE

Create the following files:

app/
main.py
esi.py
scoring.py
models.py

---

## REQUIREMENTS

### 1. ESI DATA FETCHING (esi.py)

Implement async functions:

* get_system_kills()
  GET https://esi.evetech.net/latest/universe/system_kills/

* get_system_jumps()
  GET https://esi.evetech.net/latest/universe/system_jumps/

Handle:

* timeouts
* retries (at least 2)
* basic error handling

---

### 2. DATA MODEL (models.py)

Create a Pydantic model:

SystemStats:

* system_id: int
* ship_kills: int
* pod_kills: int
* npc_kills: int
* jumps: int
* score: float

---

### 3. SCORING LOGIC (scoring.py)

Implement function:

calculate_score(system):

score = npc_kills * 3
- jumps * 1.5
- ship_kills * 8
- pod_kills * 10

Also:

* filter out systems where npc_kills == 0
* return sorted list (descending score)

---

### 4. API (main.py)

Create FastAPI app with endpoints:

GET /health
→ returns {"status": "ok"}

GET /targets
→ returns top 20 systems sorted by score

Flow:

* fetch kills + jumps
* merge by system_id
* compute score
* return JSON

---

### 5. PERFORMANCE

* Use async everywhere
* Do NOT block
* Add simple in-memory cache (TTL = 10 minutes)

---

### 6. OUTPUT FORMAT

Example:

[
{
"system_id": 30000142,
"npc_kills": 120,
"ship_kills": 0,
"pod_kills": 0,
"jumps": 3,
"score": 330.0
}
]

---

### 7. CONSTRAINTS

* No database (for now)
* No frontend
* No authentication
* Keep code clean and modular

---

## BONUS (if time)

* Add query param: /targets?limit=50
* Add logging
* Add basic validation

---

## STYLE

* Clean, readable code
* Type hints everywhere
* No unnecessary complexity

---

## FINAL OUTPUT

Return all files fully implemented:

* main.py
* esi.py
* scoring.py
* models.py

Do not explain — just generate working code.
