# fobJob_full_prod — Production-ready (FastAPI + React built + Nginx + Scheduler)

## Run everything with Docker Compose
```bash
docker compose up --build
```
- Frontend (served by nginx): http://localhost:5173
- Backend API: http://localhost:8000
  - GET /health
  - GET /cars
  - POST /cars/refresh (also called by scheduler every 6 hours)

## Data persistence
SQLite DB stored in `./backend/data/data.db` on host (volume mount).

## Notes
- The scheduler container uses a simple loop to POST to `/cars/refresh` every 21600 seconds (6 hours).
- If you prefer cron-based scheduling, we can replace scheduler with a tiny Alpine image + crond.
- Nginx serves the frontend build on port 5173. If you want it on port 80, change ports mapping in docker-compose.
