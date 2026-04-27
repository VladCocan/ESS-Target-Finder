<div align="center">

```
╔═══════════════════════════════════════════════════════╗
║    ⊕  E S S   T A R G E T   F I N D E R              ║
║       NULL-SEC INTELLIGENCE · ESI LIVE DATA           ║
╚═══════════════════════════════════════════════════════╝
```

**Identify optimal ESS robbery targets in EVE Online using real-time ESI intelligence and a dark tactical HUD UI.**

[![FastAPI](https://img.shields.io/badge/FastAPI-0D1520?style=flat-square&logo=fastapi&logoColor=00B4FF)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-0D1520?style=flat-square&logo=docker&logoColor=00B4FF)](https://www.docker.com)
[![SQLite](https://img.shields.io/badge/SQLite-0D1520?style=flat-square&logo=sqlite&logoColor=00B4FF)](https://sqlite.org)
[![EVE ESI](https://img.shields.io/badge/EVE_ESI-LIVE-3A8C6A?style=flat-square)](https://esi.evetech.net)

</div>

---

## `// OVERVIEW`

ESS Target Finder scores null-sec systems for Emergency Suppression Sentry robbery viability.
It pulls live kill and jump data from the EVE ESI API, applies a distance-aware scoring algorithm,
and surfaces a ranked target list in a branded, dark command-center interface.

The frontend uses a static Nginx site with design tokens, Orbitron/Share Tech Mono/Rajdhani fonts,
brand assets under `frontend/brand/`, and a live `nearby` target lookup page.

---

## `// FEATURES`

| Module | Description |
|--------|-------------|
| `KILL SCAN` | Fetch real-time system kill activity via ESI |
| `JUMP INTEL` | Monitor jump activity and traffic patterns |
| `SCORE ENGINE` | Rank systems by ESS robbery viability score |
| `NULL-SEC FILTER` | Automatically exclude non-null-sec systems |
| `DISTANCE SCORING` | Penalise targets far from your staging system |
| `THEMED UI` | Brand-driven dark tactical dashboard |
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

## `// FRONTEND DESIGN`

The frontend is built as a branded dashboard with:

- `frontend/css/tokens.css` for colors, typography, spacing, and UI tokens
- `frontend/style.css` for layout, hero animation, badge system, and table styling
- `frontend/brand/` assets for logos, favicons, and OG preview imagery
- `frontend/index.html` for the main target dashboard
- `frontend/nearby.html` for nearby targets filtering

The design is based on the brand reference page at `frontend/brand/docs/index.html`
and the guide in `frontend/brand/BRAND-GUIDELINES.md`.

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
│  ├── Nginx            Static site server    │
│  ├── Vanilla JS       Fetch + render logic  │
│  └── CSS tokens       Branded design system  │
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
│   ├── app/
│   │   ├── db.py          ← SQLite metadata storage
│   │   ├── esi.py         ← ESI API client
│   │   ├── main.py        ← FastAPI app + routes
│   │   ├── models.py      ← request/response models
│   │   └── scoring.py     ← target scoring logic
│   └── Dockerfile
├── docker-compose.yml
├── frontend/
│   ├── app.js             ← Main target dashboard logic
│   ├── nearby.js          ← Nearby target logic
│   ├── index.html         ← Main UI page
│   ├── nearby.html        ← Nearby targets page
│   ├── style.css          ← Brand UI styling
│   ├── Dockerfile         ← Frontend container build
│   ├── css/tokens.css     ← Design tokens and brand variables
│   └── brand/
│       ├── BRAND-GUIDELINES.md
│       ├── docs/index.html
│       ├── favicons/
│       └── svg/
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

The backend filters to null-sec systems before scoring and sorts results descending by score.

---

## `// DISCLAIMER`

> ESS Target Finder is an independent tool built by the EVE community.
> It is not affiliated with, endorsed by, or connected to CCP Games.
> All game data is fetched from the public [EVE ESI API](https://esi.evetech.net).

---

<div align="center">

```
· · · · · · · · · · · · · · · · · · · · · · · · · · · · ·
  ESS TARGET FINDER  ·  © 2026 VladCocan
  github.com/VladCocan/ESS-Target-Finder
· · · · · · · · · · · · · · · · · · · · · · · · · · · · ·
```

</div>
