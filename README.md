<div align="center">

```
╔═══════════════════════════════════════════════════════╗
║    ⊕  E S S   T A R G E T   F I N D E R              ║
║       NULL-SEC INTELLIGENCE · ESI LIVE DATA           ║
╚═══════════════════════════════════════════════════════╝
```

**Identify optimal ESS robbery targets in EVE Online using real-time ESI intelligence.**

[![FastAPI](https://img.shields.io/badge/FastAPI-0D1520?style=flat-square&logo=fastapi&logoColor=00B4FF)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-0D1520?style=flat-square&logo=docker&logoColor=00B4FF)](https://www.docker.com)
[![SQLite](https://img.shields.io/badge/SQLite-0D1520?style=flat-square&logo=sqlite&logoColor=00B4FF)](https://sqlite.org)
[![EVE ESI](https://img.shields.io/badge/EVE_ESI-LIVE-3A8C6A?style=flat-square)](https://esi.evetech.net)

</div>

---

## `// OVERVIEW`

ESS Target Finder scores null-sec systems for Emergency Suppression Sentry robbery viability.
It pulls live kill and jump data from the EVE ESI API, applies a distance-aware scoring algorithm,
and returns a ranked list of targets — so you know exactly where to go before your enemies do.

---

## `// FEATURES`

| Module | Description |
|--------|-------------|
| `KILL SCAN` | Fetch real-time system kill activity via ESI |
| `JUMP INTEL` | Monitor jump traffic to detect active corridors |
| `SCORE ENGINE` | Rank systems by ESS robbery viability score (0–100) |
| `NULL-SEC FILTER` | Automatically exclude non-null-sec systems |
| `DISTANCE SCORING` | Penalise targets far from your staging system |
| `METADATA CACHE` | SQLite caching for fast repeated lookups |
| `DOCKER STACK` | One-command deploy — backend + frontend |

---

## `// QUICK START`

### Requirements

- [Docker](https://docs.docker.com/get-docker/) + Docker Compose

### Deploy

```bash
git clone https://github.com/VladCocan/ESS-Target-Finder.git
cd ESS-Target-Finder
docker compose up --build
```

### Access

| Service | URL |
|---------|-----|
| Frontend | [http://localhost:3000](http://localhost:3000) |
| Backend API | [http://localhost:8000](http://localhost:8000) |
| API Docs | [http://localhost:8000/docs](http://localhost:8000/docs) |

---

## `// API USAGE`

### GET /targets

Returns a scored and ranked list of ESS robbery targets.

```http
GET /targets?from_system=Jita
```

**Parameters**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `from_system` | `string` | ✓ | Staging system name (e.g. `Jita`) |

**Response**

```json
[
  {
    "system_name": "GE-8JV",
    "region": "Catch",
    "score": 97,
    "kills_1h": 42,
    "jumps_1h": 3,
    "distance_ly": 4.1,
    "security": -0.34
  },
  {
    "system_name": "HED-GP",
    "region": "Catch",
    "score": 89,
    "kills_1h": 31,
    "jumps_1h": 8,
    "distance_ly": 6.0,
    "security": -0.28
  }
]
```

**Score Legend**

```
▓▓▓▓▓▓▓▓▓▓  80–100  ·  HIGH RISK / HIGH REWARD
▒▒▒▒▒▒░░░░  40–79   ·  MEDIUM — worth scouting
░░░░░░░░░░  0–39    ·  LOW — low activity or far range
```

---

## `// TECH STACK`

```
┌─────────────────────────────────────────────┐
│  BACKEND                                    │
│  ├── FastAPI          Python async API      │
│  ├── httpx            Async ESI requests    │
│  └── SQLite           Metadata caching      │
│                                             │
│  FRONTEND                                   │
│  └── Vanilla JS       No-dependency UI      │
│                                             │
│  INFRA                                      │
│  └── Docker Compose   One-command deploy    │
└─────────────────────────────────────────────┘
```

---

## `// PROJECT STRUCTURE`

```
ESS-Target-Finder/
├── backend/
│   ├── main.py          ← FastAPI app + routes
│   ├── esi.py           ← ESI API client
│   ├── scorer.py        ← Target scoring logic
│   └── cache.py         ← SQLite metadata cache
├── frontend/
│   ├── index.html       ← Main UI
│   └── app.js           ← Fetch + render logic
├── docker-compose.yml
└── README.md
```

---

## `// SCORING ALGORITHM`

The score for each system is computed as:

```
score = (kill_weight × kills_1h)
      + (jump_weight × jumps_1h)
      - (distance_penalty × distance_ly)
```

Systems are filtered to null-sec only (`security < 0.0`) before scoring.
Results are sorted descending by score.

---

## `// DISCLAIMER`

> ESS Target Finder is an independent tool built by the EVE community.
> It is not affiliated with, endorsed by, or connected to CCP Games.
> All game data is fetched from the public [EVE ESI API](https://esi.evetech.net).

---

<div align="center">

```
· · · · · · · · · · · · · · · · · · · · · · · ·
  ESS TARGET FINDER  ·  © 2026 VladCocan
  github.com/VladCocan/ESS-Target-Finder
· · · · · · · · · · · · · · · · · · · · · · · ·
```

</div>