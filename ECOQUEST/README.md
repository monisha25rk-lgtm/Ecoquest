# EcoQuest — Person 1 student module

EcoQuest connects students with community-oriented college events. This repository implements Person 1's student-facing module: student accounts, event discovery, registration, and in-app notifications.

Eco Points are EcoQuest platform rewards. They are **not** official VTU/AICTE academic activity points, and this module does not certify academic credit.

## Stack

- Frontend: React 18, Vite, JavaScript, React Router, Lucide React
- Backend: FastAPI, SQLAlchemy 2, Pydantic
- Database: SQLite
- Authentication: JWT and Argon2 (`pwdlib`)
- Tests: Pytest and FastAPI TestClient

## Structure

```text
frontend/                 React/Vite student experience
backend/app/              FastAPI application
backend/app/models/       Person 1 SQLAlchemy models
backend/tests/            Backend API tests
docs/                     API, schema, and integration documentation
backend/ecoquest.db       Local shared SQLite database (created at startup)
```

## Setup

Use Python 3.10+ and Node.js 18+.

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Set a private `SECRET_KEY` in `backend/.env` before using authentication. A random key can be generated with:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Start the API from the `backend` directory:

```powershell
uvicorn app.main:app --reload
```

The API is at `http://127.0.0.1:8000`; Swagger UI is at `http://127.0.0.1:8000/docs`.

### Frontend

In another terminal:

```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```

The Vite development server is at `http://localhost:5173`.

### Tests

```powershell
cd backend
pytest -q
```

Tests use an in-memory SQLite database and a test-only `events` table fixture. Production does not create an `events` table.

## Environment

Backend variables are in `backend/.env.example`:

- `DATABASE_URL`: by default the database URL is resolved to the shared `backend/ecoquest.db` file.
- `SECRET_KEY`: required for JWT issuance and validation. Never commit a real value.
- `ALGORITHM`: JWT signing algorithm (default `HS256`).
- `ACCESS_TOKEN_EXPIRE_MINUTES`: token lifetime (default 30).
- `FRONTEND_URL`: allowed development CORS origin.

Frontend variables are in `frontend/.env.example`:

- `VITE_API_BASE_URL`: FastAPI base URL.
- `VITE_GAMIFICATION_SUMMARY_URL`, `VITE_GAMIFICATION_BADGES_URL`, `VITE_GAMIFICATION_LEADERBOARD_URL`: set only to endpoints and response contracts agreed with Person 3. Unconfigured gamification values are shown as unavailable, not fabricated.

## API and database

- API details: [docs/API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md)
- Database ownership and schema: [docs/DATABASE_SCHEMA.md](docs/DATABASE_SCHEMA.md)
- Team integration requirements: [docs/INTEGRATION_GUIDE.md](docs/INTEGRATION_GUIDE.md)

## Person 2 implementation

Person 1 owns `users`, `categories`, `event_registrations`, and `notifications`. The application initializes accounts and categories immediately. Registration and notification tables are initialized only after the shared `events` table is present.

Person 2 owns `organizations`, `events`, `progress_logs`, `submissions`, `submission_files`, and `reviews`; see [docs/PERSON2_INTEGRATION.md](docs/PERSON2_INTEGRATION.md). Person 3 still owns points, badges, leaderboards, and reports. The reward hook passes an approved registration ID to Person 3 and does not calculate points locally.
