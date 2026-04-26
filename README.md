# ESS Target Finder

A tool that identifies optimal ESS robbery targets in EVE Online using ESI data.

## Features

* Fetch system activity (kills, jumps)
* Score systems for ESS robbery
* Filter null-sec systems
* Distance-aware scoring
* Dockerized backend and frontend
* SQLite metadata caching

## How to run

```bash
docker compose up --build
```

## Access

Backend API:
http://localhost:8000

Frontend:
http://localhost:3000

## Example API usage

GET /targets?from_system=Jita

## Tech stack

* FastAPI
* httpx
* SQLite
* Docker
* Vanilla JS frontend
