# AI Agent Guide: coffee-recommender-api

Welcome! This file provides a comprehensive overview of the `coffee-recommender-api` codebase, including the technology stack, project structure, instructions for running/building, testing, database migration commands, and architectural rules to follow during development.

---

## 🛠️ Technology Stack & Dependencies

- **Framework**: FastAPI (v0.115.6)
- **ASGI Server**: Uvicorn (v0.34.0)
- **Language**: Python (v3.12)
- **Database**: PostgreSQL (v16)
- **ORM / Driver**: SQLAlchemy (v2.0.36) with `asyncpg` (async engine) & `psycopg2-binary` (sync driver for Alembic/scripts)
- **Migrations**: Alembic (v1.14.1)
- **Admin Panel**: SQLAdmin (v0.20.1) accessible at `/admin`
- **Config & Settings**: Pydantic Settings (v2.7.1) + python-dotenv
- **Security & JWT**: `python-jose[cryptography]` + `passlib[bcrypt]`
- **Testing**: `pytest`, `pytest-asyncio`, `aiosqlite` (in-memory async DB), `httpx`

---

## 📂 Directory & File Structure

```text
coffee-recommender-api/
├── app/                      # Main application package
│   ├── repositories/         # [NEW] Data Access Layer (Repository Pattern)
│   │   ├── base.py           # Generic BaseRepository with async CRUD operations
│   │   ├── shop_repository.py      # Shop queries (filters, geo-distance, distinct options)
│   │   ├── suggestion_repository.py # ShopSuggestion queries
│   │   └── review_repository.py     # Review database queries
│   ├── services/             # [NEW] Business Logic Layer (Service Pattern)
│   │   ├── shop_service.py   # Shop management, slugify, filter assembly
│   │   ├── suggestion_service.py # User suggestions, suggestion approvals/rejections
│   │   └── review_service.py # Review validations & commits
│   ├── routers/              # FastAPI router modules
│   │   ├── auth.py           # JWT-based authentication (/api/auth/login)
│   │   ├── shops.py          # Shop retrieval, filters, review creation
│   │   ├── suggestions.py    # Public suggestion submission
│   │   └── admin.py          # [PROTECTED] Admin suggestion listing/approval/rejection
│   ├── models.py             # SQLAlchemy models (Table structures)
│   ├── schemas.py            # Pydantic schemas (Request/Response validation)
│   ├── database.py           # Async engine and sessionmaker config
│   ├── config.py             # Pydantic-based configuration (cached with @lru_cache)
│   ├── security.py           # Password hashing (bcrypt) and JWT helpers
│   ├── dependencies.py       # [NEW] Injectables (get_current_user, get_current_admin)
│   ├── seed.py               # Data seeding script (populated from crawled_shops.json)
│   ├── main.py               # API Entrypoint (fastapi setup, lifespan, global exception handler)
│   └── utils.py              # Helper utilities (VN timezone checks, opening hours parser)
├── tests/                    # [NEW] Automated Test Suite
│   ├── conftest.py           # Fixtures for clients, token helpers, and SQLite in-memory DB
│   ├── test_auth.py          # Tests for login validation
│   ├── test_shops.py         # Tests for shops retrieval and filter options
│   └── test_suggestions.py   # Tests for suggestion routing and permission gates
├── alembic/                  # Alembic DB migration versions and env.py
├── crawled_shops.json        # Main seed source data containing coffee shop details
├── docker-compose.yml        # Docker composition (Postgres & API service)
├── Dockerfile                # Multi-stage build configuration for Python environment
├── requirements.txt          # Python package dependencies
├── alembic.ini               # Alembic configuration
├── seed_admin.py             # Standalone script to seed superuser account
└── update_shops.py           # Enriches crawled_shops.json with drink & pastry menus
```

---

## ⚙️ Environment Variables (`.env`)

A default `.env` file should contain the following settings:
```ini
POSTGRES_USER=danang_coffee
POSTGRES_PASSWORD=danang_coffee_2024
POSTGRES_DB=danang_coffee

# DB URL for docker containers (host 'coffee-db')
DATABASE_URL=postgresql+asyncpg://danang_coffee:danang_coffee_2024@coffee-db:5432/danang_coffee
DATABASE_URL_SYNC=postgresql://danang_coffee:danang_coffee_2024@coffee-db:5432/danang_coffee

# Admin Security
SECRET_KEY=super-secret-key-for-admin-sessions-12345
```

---

## 🚀 How to Run & Build

### Option 1: Running with Docker Compose (Recommended)
This spins up PostgreSQL (`coffee-db`) and FastAPI (`coffee-api`) containers. It also runs database migrations and seeds initial data automatically.

```bash
# Start all containers in detached mode and rebuild images
docker compose up --build -d

# View container logs
docker compose logs -f

# Stop containers
docker compose down
```

### Option 2: Running Locally (Host Environment)
If running directly on the host (e.g. for step-by-step debugging):

1. **Virtual Environment Setup**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure `.env`**:
   If PostgreSQL is running in Docker but the API runs on the host, point the database host to `localhost` and port `5433` (as exposed by `docker-compose.yml`):
   ```ini
   DATABASE_URL=postgresql+asyncpg://danang_coffee:danang_coffee_2024@localhost:5433/danang_coffee
   DATABASE_URL_SYNC=postgresql://danang_coffee:danang_coffee_2024@localhost:5433/danang_coffee
   SECRET_KEY=your-local-development-secret-key
   ```

3. **Database Setup (Migrations & Seeding)**:
   ```bash
   # Apply database migrations
   alembic upgrade head

   # Seed initial coffee shops (crawled_shops.json)
   python -m app.seed

   # Seed default admin user
   python seed_admin.py
   ```

4. **Start Development Server**:
   ```bash
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```
   - API Docs will be available at: `http://localhost:8000/docs`
   - Admin Panel: `http://localhost:8000/admin` (Sign in using admin credentials generated by seed_admin.py)

---

## 🧪 Testing

The API uses `pytest` and `pytest-asyncio` with an async in-memory SQLite database setup (`aiosqlite`). Tests are entirely isolated and do not modify the main development/production databases.

To run the test suite:
```bash
pytest tests/ -v
```

---

## 🔄 Database Migrations (Alembic)

Always use Alembic to make schema changes. Never update database tables manually.

### Generating a New Migration
When you modify or add database models in `app/models.py`, generate a new migration file:
```bash
alembic revision --autogenerate -m "describe_your_changes_here"
```

### Applying Migrations
```bash
alembic upgrade head
```

### Downgrading Migrations
```bash
alembic downgrade -1
```

---

## 🚨 Critical Architectural Rules for AI Agents

> [!CAUTION]
> **Always Check Docker Logs for Debugging**: Whenever a backend error, crash, restart loop, or test failure occurs, you MUST inspect the Docker logs (`docker compose logs coffee-api` or `docker compose logs -f`) before making code modifications. Do not guess the cause of runtime errors or database connection failures.

> [!IMPORTANT]
> **Repository & Service Pattern**: Do not add raw database queries or direct CRUD logic inside FastAPI routers. All database access must go through the appropriate repository class under `app/repositories/`, and all business logic (such as validations, updates, formatting) must go through the appropriate service class under `app/services/`.

> [!IMPORTANT]
> **Use Asynchronous Queries**: All database queries must run asynchronously using SQLAlchemy's async engine (e.g., `await session.execute()`). Do NOT block the event loop with synchronous queries.

> [!WARNING]
> **JWT Authentication Required**: Admin endpoints (under `/api/admin/`) MUST be protected using FastAPI's dependency injection with `get_current_admin` (`Depends(get_current_admin)`). Unprotected admin endpoints will fail security compliance reviews.

> [!WARNING]
> **UTC Datetime best practice**: Do not use `datetime.utcnow()` or `datetime.utcfromtimestamp()` as they are deprecated. Use timezone-aware timestamps with `datetime.now(timezone.utc)` (imported from `datetime` and `timezone` from the `datetime` standard library).

> [!NOTE]
> **Caching Configuration**: Always import `settings` by using `from app.config import get_settings` and calling `settings = get_settings()`. This utilizes `@lru_cache` to avoid repeated IO and object initialization overhead.
