# AGENTS.md — Gestor EFITA

High-signal guidance for agents working in this FastAPI + Vanilla JS event management system.

## Project Structure

**Monorepo with clear separation:**
- `backend/` — FastAPI REST API (Python 3.10+, SQLAlchemy ORM, SQLite, pytest)
- `frontend/` — Vanilla JS + Vite, multiple entry points (registration, status check, admin panel)
- `docker-compose.yml` — Local dev setup; backend on 8000, frontend on 8080

**Key files:**
- `backend/app/main.py` — FastAPI app initialization, CORS, rate limiting setup
- `backend/app/routers/` — Two routers: `inscricao.py` (public routes), `admin.py` (authenticated)
- `backend/tests/conftest.py` — pytest fixtures, DB setup (in-memory SQLite), test client with JWT
- `frontend/vite.config.js` — Multi-page build config with proxy to `/api` → `http://localhost:8000`

## Running the System

### Local Manual Setup (No Docker)

**Backend:**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env  # Adjust DATABASE_URL and FRONTEND_ORIGIN if needed
python seed_admin.py  # Create initial admin user (interactive)
python run.py  # Starts uvicorn on http://localhost:8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev  # Starts Vite dev server (usually http://localhost:5173)
# Vite proxies /api requests to http://localhost:8000
```

### Docker Compose
```bash
docker-compose up --build -d
docker exec -it efita_backend python seed_admin.py  # Create admin
# Frontend: http://localhost:8080, Backend: http://localhost:8000
```

## Testing

**Run all backend tests:**
```bash
cd backend
pytest tests/ -v
```

**Key test setup facts:**
- In-memory SQLite DB per test (conftest.py:23–27)
- Rate limiters disabled during tests (conftest.py:17–19)
- `client` fixture provides TestClient with test DB override
- `admin_token` fixture creates test admin and returns JWT
- Use `@patch()` for email service (async mock in test payloads)

**Test file layout:**
- `test_inscricao.py` — Public registration routes, CSV export
- `test_admin.py` — Admin login, dashboard, status updates
- `test_services.py` — Email service, participant helpers

## Code Conventions

**Python (Backend):**
- Routers use `APIRouter(prefix="/api/...")` with tag names
- Fixtures in test payloads (PAYLOAD_EXTERNO, PAYLOAD_ITA_GRAD, etc.)
- Test classes grouped by endpoint, e.g. `class TestCriarInscricao`
- Service layer in `app/services/` (participante, email)
- Schemas use Pydantic with docstring examples

**JavaScript (Frontend):**
- Vanilla JS, no framework; HTML templates in `*.html`
- Vite dev server proxies API calls; no explicit URL construction for `/api/*`
- Multiple entry points (index.html, consulta.html, admin/login.html, admin/dashboard.html)

## Critical Rules

**Test coverage (non-negotiable):**
- No code change without corresponding tests
- New features: unit + integration tests covering success and failure paths
- Bug fixes: create failing test first that reproduces the issue, then fix

**Database & ORM:**
- SQLAlchemy models in `app/models.py`
- Session dependency injected via `get_db()` from `app/dependencies.py`
- Tests use in-memory DB; Docker uses volume-mounted SQLite at `/app/data/efita.db`

**Email Service:**
- Async queue-based (background worker); started/stopped in FastAPI lifespan
- Always mock with `@patch("app.services.email.email_service.enqueue")` in tests
- Payloads enqueued via `email_service.enqueue(to, subject, template, context)`

**CORS & Rate Limiting:**
- CORS origin from `settings.FRONTEND_ORIGIN` (env var, default `http://localhost:8080`)
- Rate limiting via `slowapi`; disabled in tests
- Main limiter in main.py, inscricao-specific limiter in routers/inscricao.py

**CPF Validation:**
- Strict validation using Módulo 11 algorithm (checksum).
- Schemas (`InscricaoCreate`) automatically normalize (remove `.` and `-`) and validate CPFs.
- **Critical:** Tests MUST use truly valid CPFs. Sequences like `000.000.000-00` or random 11-digit numbers will fail and cause `422 Unprocessable Entity`.
- **How to generate valid CPFs for tests:** Run the script in the backend folder:
  ```bash
  cd backend
  python gen_cpf.py
  ```


## Common Commands

```bash
# Backend
cd backend
pytest tests/ -v                 # Run all tests
pytest tests/test_admin.py -v   # Run specific test file
python run.py                   # Dev server with hot reload
python seed_admin.py            # Interactive admin creation
python force_seed.py            # Force create admin (user: admin, pass: admin)

# Frontend
cd frontend
npm run dev                      # Dev server (port 5173)
npm run build                   # Production build to dist/
npm run preview                 # Preview production build

# Docker
docker-compose up --build -d    # Start services
docker-compose down             # Stop and remove containers
docker exec -it efita_backend python seed_admin.py  # Admin from running container
```

## Known Quirks & Gotchas

- **Port 5173 vs 8080:** Vite dev server runs on 5173 by default, but production (Docker) frontend is on 8080 via nginx
- **Proxy in dev:** Frontend Vite proxies `/api` to `http://localhost:8000`; never hardcode API URLs
- **env_file in docker-compose:** Backend loads `.env` from `./backend/.env`; use for secrets or non-standard DATABASE_URL
- **Tests disable rate limiting:** If testing rate limit behavior, explicitly re-enable limiters
- **Multi-page Vite:** Four separate entry points; CSS/JS imports must be per-page or bundled explicitly
