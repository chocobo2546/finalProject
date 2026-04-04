# Project Setup Guide

## Option 1: Run with Docker (Recommended)

Run the entire application stack (frontend, backend, scheduler, and database) using Docker Compose:

```bash
docker compose up --build
```

### Services

* Frontend (served via Nginx): http://localhost:5173
* Backend API: http://localhost:8000

  * `GET /health`
  * `GET /cars`
  * `POST /cars/refresh` (also triggered automatically every 6 hours)

### Data Persistence

* SQLite database is stored at:
  `./backend/data/data.db` (mounted as a volume on the host)

### Notes

* A scheduler container sends a request to `/cars/refresh` every 21600 seconds (6 hours)
* You can switch to cron-based scheduling if preferred
* To change frontend port (e.g., to port 80), modify the `ports` section in `docker-compose.yml`

---

## Option 2: Run Without Docker (Manual Setup)

You can also run the application manually without Docker.

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Backend will be available at:
http://localhost:8000

---

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend will be available at:
http://localhost:5173

---

## Notes for Manual Setup

* Ensure Python and Node.js are installed on your system
* The frontend is configured to connect to the backend at `http://localhost:8000`
* The scheduler will **not run automatically** in this mode (you must trigger `/cars/refresh` manually or implement your own scheduler)

---

