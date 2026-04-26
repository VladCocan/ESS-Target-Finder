You are a senior backend + DevOps engineer.

You are given an existing FastAPI project called **ESS-Target-Finder**.

Your task is to REFINE, FIX, and EXTEND it into a production-ready MVP.

DO NOT rewrite everything. Improve what exists.

---

# GOALS

1. Fix concurrency and correctness issues
2. Make the backend robust and production-ready
3. Add EVE-specific filtering (null-sec focus)
4. Add Docker support
5. Add a simple frontend UI
6. Keep everything minimal and clean

---

# EXISTING STRUCTURE

app/

* main.py
* esi.py
* scoring.py
* models.py

---

# REQUIRED IMPROVEMENTS

## 1. FIX ASYNC (CRITICAL)

Replace sequential awaits with proper concurrency:

Use asyncio.gather() when fetching ESI data.

---

## 2. FIX CACHE (CRITICAL)

Current cache is unsafe.

Implement:

* global in-memory cache
* TTL = 10 minutes
* asyncio.Lock to prevent race conditions

---

## 3. IMPROVE ESI CLIENT

In esi.py:

* Add exponential backoff
* Improve timeout granularity
* Handle HTTP errors cleanly
* Return empty list on failure (no crash)

---

## 4. ADD NULL-SEC FILTERING (IMPORTANT)

Modify scoring pipeline:

* filter only systems with security < 0.0

You can hardcode a minimal mapping OR create placeholder function:
is_nullsec(system_id) → bool

Keep it simple but extensible.

---

## 5. IMPROVE SCORING

Keep formula but:

* move weights to constants
* make function clean and testable

---

## 6. ADD LOGGING

* log ESI fetches
* log cache hits
* log number of systems processed

---

## 7. ADD DOCKER SUPPORT

Create:

backend/Dockerfile

Requirements:

* python:3.12-slim
* install dependencies
* run uvicorn app.main:app --host 0.0.0.0 --port 8000

Create requirements.txt

---

## 8. ADD FRONTEND (MINIMAL)

Create folder:

frontend/

Files:

* index.html
* app.js
* style.css

Requirements:

* Fetch from: http://localhost:8000/targets
* Display table
* Columns:
  system_id, npc_kills, ship_kills, pod_kills, jumps, score
* Sort by score descending
* Add refresh button
* Add loading indicator

Use plain JS (no frameworks)

---

## 9. DOCKERIZE FRONTEND

Dockerfile:

* nginx:alpine
* serve static files

---

## 10. DOCKER COMPOSE

Create docker-compose.yml:

services:

backend:

* build ./backend
* ports 8000:8000

frontend:

* build ./frontend
* ports 3000:80
* depends_on backend

---

## 11. ENABLE CORS

In FastAPI:

Allow origin:
http://localhost:3000

---

# OUTPUT FORMAT

Return ALL updated and new files:

* app/main.py (fixed)
* app/esi.py (improved)
* app/scoring.py (cleaned)
* app/models.py (if needed)
* backend/Dockerfile
* backend/requirements.txt
* frontend/index.html
* frontend/app.js
* frontend/style.css
* frontend/Dockerfile
* docker-compose.yml

---

# STYLE

* clean
* readable
* minimal
* no overengineering

---

# IMPORTANT

* do not explain anything
* only output code
* ensure everything runs with: docker-compose up
