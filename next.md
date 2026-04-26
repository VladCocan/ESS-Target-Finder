You are a senior full-stack engineer.

Extend an existing FastAPI backend project called **ESS-Target-Finder** into a full Dockerized application with a minimal frontend.

## GOAL

1. Containerize the backend properly
2. Add a simple frontend UI to display target systems
3. Run everything with docker-compose

---

## BACKEND (already exists)

FastAPI app with:

* /health
* /targets

DO NOT rewrite backend logic unless needed.

---

## REQUIREMENTS

### 1. DOCKERIZE BACKEND

Create:

Dockerfile (for FastAPI app)

Requirements:

* Python 3.12 slim
* Install dependencies with pip
* Copy app code
* Run with uvicorn:
  uvicorn app.main:app --host 0.0.0.0 --port 8000

---

### 2. REQUIREMENTS.TXT

Create a requirements.txt with:

* fastapi
* uvicorn
* httpx
* pydantic

---

### 3. FRONTEND (simple and clean)

Create a minimal frontend using:

OPTION A (preferred): plain HTML + JS
OPTION B: simple React (only if small)

Requirements:

* Fetch data from: /targets
* Display table:

Columns:

* system_id

* npc_kills

* ship_kills

* pod_kills

* jumps

* score

* Add refresh button

* Add loading indicator

* Sort by score descending (client-side)

---

### 4. FRONTEND STRUCTURE

frontend/
index.html
app.js
style.css

Use fetch API (no libraries)

---

### 5. DOCKERIZE FRONTEND

Create Dockerfile for frontend:

* Use nginx:alpine
* Copy static files to /usr/share/nginx/html

---

### 6. DOCKER COMPOSE

Create docker-compose.yml with:

services:

backend:

* build: ./backend
* ports: 8000:8000

frontend:

* build: ./frontend
* ports: 3000:80
* depends_on: backend

---

### 7. CORS (IMPORTANT)

Modify FastAPI app:

* allow frontend access
* use CORSMiddleware

allow:

* http://localhost:3000

---

### 8. OUTPUT FORMAT

Return ALL files fully implemented:

* backend/Dockerfile
* backend/requirements.txt
* frontend/Dockerfile
* frontend/index.html
* frontend/app.js
* frontend/style.css
* docker-compose.yml

---

## STYLE

* Clean
* Minimal
* Working
* No overengineering

---

## IMPORTANT

* Do NOT explain anything
* Only output code
* All files must be complete and runnable
