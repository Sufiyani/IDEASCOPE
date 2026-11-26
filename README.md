# IdeaScope — FYP Readiness System
**Sir Syed University of Engineering & Technology — Software Engineering Department**

---

## What is IdeaScope?

Students upload their FYP project idea (PDF / DOCX / TXT) along with a short form. The system compares it against a knowledge base of past FYP projects using AI and returns a **Readiness Report** that tells the student:

- Which past projects are similar and how similar (score + risk band)
- Which of their proposed features are **Matched / Partial / Not mentioned** compared to past work
- Suggested **project category** and **SDGs** (with yearly quota availability)
- AI-generated **feature improvement suggestions**

The student then confirms their **Final Scope** (features, objectives, category, SDGs) through the platform. Admins manage past project data, user accounts, yearly quotas, and system settings.

---

## Team & Ownership

| Member | Name | Role in Codebase |
|--------|------|-----------------|
| **M1** | M Naqi Rahmani | AI layer, Readiness Report, Deploy |
| **M2** | Sufiyan Imran | Auth, Users, Worker, Docker, Core |
| **M3** | Sarmad Arshad | Ingestion, Proposals, Quotas, Settings |

> Full file-level ownership is in `CODEOWNERS`. One module = one owner. Changes to shared code (`core/`, shared models) require a PR reviewed by another member.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic |
| Database | PostgreSQL 16 + pgvector |
| Auth | JWT (access + refresh), bcrypt, role-based (student / admin / main_admin) |
| AI | Claude API (or Mock for dev), BGE-M3 embeddings, hybrid search |
| Background Jobs | Custom worker polling a `jobs` table |
| File Parsing | pdfplumber, python-docx, openpyxl / pandas |
| Frontend | React + Vite |
| DevOps | Docker + docker-compose, Nginx, Let's Encrypt (Contabo VPS) |

---

## Project Structure

```
ideascope/
│
├── backend/
│   ├── app/
│   │   ├── core/               Config, JWT/bcrypt, deps, audit log        [M2]
│   │   ├── models/             SQLAlchemy ORM models (one file per table)  [M1/M2/M3]
│   │   ├── schemas/            Pydantic request/response shapes            [M1/M2/M3]
│   │   ├── routers/            FastAPI route definitions                   [M1/M2/M3]
│   │   ├── services/           Business logic (called by routers)          [M1/M2/M3]
│   │   ├── worker/             Background job runner + registry            [M2]
│   │   ├── ai/                 LLM providers, pipelines, search, scoring   [M1]
│   │   │   ├── providers/      base, claude, mock, factory
│   │   │   ├── prompts/        Prompt files (.md) — one per AI task
│   │   │   └── evaluation/     Test ideas + expected answers for AI testing
│   │   ├── ingestion/          Excel/CSV import, dedup, normalize, extract [M3]
│   │   └── main.py             FastAPI app entry point                     [M2]
│   │
│   ├── alembic/                DB migration setup + versions/              [M2]
│   ├── scripts/                setup_initial_data.py (admin, categories, SDGs) [M2]
│   ├── tests/                  pytest suite                                [M1/M2/M3]
│   ├── Dockerfile                                                          [M2]
│   └── requirements.txt                                                    [M2]
│
├── frontend/
│   └── src/
│       ├── api/                Axios client + one file per backend area    [M2/M3]
│       ├── auth/               AuthContext, ProtectedRoute, RoleGuard      [M2]
│       ├── components/         Shared UI: Layout, Sidebar, Table, Modal, FormFields
│       ├── pages/
│       │   ├── auth/           Login, ChangePassword                       [M2]
│       │   ├── layout/         DashboardFrame (menu + shell)               [M2]
│       │   ├── admin/          UserManagement, ExcelUpload, PastProjects,  [M2/M3]
│       │   │                   PastProjectDetail, Quotas, Settings
│       │   └── student/        CreateJoinGroup, IdeaUpload, FinalScope,    [M1/M2/M3]
│       │                       ReadinessReport, Suggestions
│       └── routes/             React Router config
│
├── deploy/                     Nginx conf, deploy guide, backup, hardening [M1]
├── postman/                    Shared Postman collection + env template     [all]
├── docs/                       API contracts, DB design notes               [all]
│
├── docker-compose.yml                                                       [M2]
├── .env.example                All required env vars (copy → .env)
├── .gitignore
├── CODEOWNERS
└── README.md
```

---

## Module Ownership Detail

### M1 — M Naqi Rahmani
| Path | What it does |
|------|-------------|
| `backend/app/ai/` | Full AI layer — providers, extraction, embeddings, search, comparison, scoring, suggestions, pipelines |
| `backend/app/ai/providers/base.py` | Abstract LLM provider interface |
| `backend/app/ai/providers/claude_provider.py` | Anthropic Claude integration |
| `backend/app/ai/providers/mock_provider.py` | Local dev mock (no API key needed) |
| `backend/app/ai/providers/factory.py` | Picks provider from `LLM_PROVIDER` env var |
| `backend/app/ai/prompts/*.md` | Prompt templates for every AI task |
| `backend/app/ai/evaluation/` | AI test runner + test ideas + expected answers |
| `backend/app/routers/reports.py` | GET report, GET suggestions, PATCH suggestion |
| `backend/app/services/report_service.py` | Assembles ReadinessReport from DB |
| `backend/app/models/analysis.py` | Analysis result per proposal |
| `backend/app/models/similar_match.py` | Per-match score rows |
| `backend/app/models/suggestion.py` | AI-generated suggestions |
| `backend/app/models/past_project_feature.py` | Extracted features from past projects |
| `backend/app/models/llm_usage.py` | Token accounting per AI call |
| `backend/tests/test_scoring.py` | Scoring + risk band tests |
| `deploy/` | Nginx, Certbot, hardening, backup script |
| `frontend/src/pages/student/ReadinessReport.jsx` | Report UI page |
| `frontend/src/pages/student/Suggestions.jsx` | Suggestions UI page |

---

### M2 — Sufiyan Imran
| Path | What it does |
|------|-------------|
| `backend/app/core/config.py` | All settings loaded from `.env` via pydantic-settings |
| `backend/app/core/security.py` | JWT create/verify, bcrypt hash/verify |
| `backend/app/core/deps.py` | `get_db`, `get_current_user`, `require_admin`, `require_main_admin` |
| `backend/app/core/audit.py` | Write audit log entries |
| `backend/app/worker/runner.py` | Polls `jobs` table and dispatches handlers |
| `backend/app/worker/registry.py` | Maps job type → handler (handlers implemented by M1) |
| `backend/app/routers/auth.py` | login, refresh, logout, me, change-password |
| `backend/app/routers/users.py` | CRUD + role + status + password reset |
| `backend/app/routers/groups.py` | Create group, manage members |
| `backend/app/routers/jobs.py` | GET job status |
| `backend/app/models/user.py` | User table (roles: student/admin/main_admin) |
| `backend/app/models/refresh_token.py` | Refresh token storage |
| `backend/app/models/group.py` | Group + GroupMember tables |
| `backend/app/models/category.py` | 12 project categories |
| `backend/app/models/sdg.py` | 17 UN SDGs |
| `backend/app/models/audit_log.py` | Audit log table |
| `backend/app/models/job.py` | Background job queue table |
| `backend/app/services/auth_service.py` | Login, token rotation, logout, change-password |
| `backend/app/services/user_service.py` | User CRUD business logic |
| `backend/app/services/group_service.py` | Group management logic |
| `backend/alembic/` | Migration env + versions |
| `backend/scripts/setup_initial_data.py` | Seeds main admin, 12 categories, 17 SDGs |
| `backend/tests/test_security.py` | JWT + bcrypt tests |
| `backend/tests/test_roles.py` | Role-based access tests |
| `backend/Dockerfile` | Backend container image |
| `docker-compose.yml` | db (pgvector), api, worker services |
| `frontend/src/auth/` | AuthContext, ProtectedRoute, RoleGuard |
| `frontend/src/pages/auth/Login.jsx` | Login page |
| `frontend/src/pages/auth/ChangePassword.jsx` | Change password page |
| `frontend/src/pages/layout/DashboardFrame.jsx` | App shell with sidebar + nav |
| `frontend/src/pages/admin/UserManagement.jsx` | Admin user management page |
| `frontend/src/pages/student/CreateJoinGroup.jsx` | Group create/join page |

---

### M3 — Sarmad Arshad
| Path | What it does |
|------|-------------|
| `backend/app/ingestion/excel_import.py` | Read Excel/CSV, map columns, batch insert |
| `backend/app/ingestion/dedupe.py` | Fuzzy duplicate detection before import |
| `backend/app/ingestion/normalize.py` | SDG text → SDG numbers, project type normalisation |
| `backend/app/ingestion/text_extract.py` | Extract text from PDF, DOCX, TXT |
| `backend/app/routers/abstracts.py` | Upload, bulk import, list, update, reprocess, delete past projects |
| `backend/app/routers/proposals.py` | Create, list, analyze, final-scope endpoints |
| `backend/app/routers/quotas.py` | List, set, status endpoints |
| `backend/app/routers/settings.py` | Get/update system settings |
| `backend/app/models/import_batch.py` | Tracks each Excel/CSV import |
| `backend/app/models/past_project.py` | Past project record (non-AI cols owned by M3; AI cols by M1) |
| `backend/app/models/proposal.py` | Student proposal submission |
| `backend/app/models/document.py` | Uploaded file metadata + extracted text |
| `backend/app/models/final_scope.py` | Confirmed scope after readiness review |
| `backend/app/models/quota.py` | Per-year per-category project slots |
| `backend/app/models/setting.py` | Key-value system settings |
| `backend/app/services/abstract_service.py` | Past project CRUD + job queuing |
| `backend/app/services/proposal_service.py` | Proposal flow + final scope |
| `backend/app/services/quota_service.py` | Quota read/write + increment |
| `backend/app/services/settings_service.py` | Settings get/upsert |
| `backend/tests/test_quota.py` | Quota logic tests |
| `backend/tests/test_ingestion.py` | Import + dedup + normalize tests |
| `frontend/src/pages/admin/ExcelUpload.jsx` | Bulk import UI |
| `frontend/src/pages/admin/PastProjects.jsx` | Past project list page |
| `frontend/src/pages/admin/PastProjectDetail.jsx` | Single past project detail |
| `frontend/src/pages/admin/Quotas.jsx` | Quota management page |
| `frontend/src/pages/admin/Settings.jsx` | System settings page |
| `frontend/src/pages/student/IdeaUpload.jsx` | File + form upload page |
| `frontend/src/pages/student/FinalScope.jsx` | Confirm final scope page |

---

## API Endpoints (Quick Reference)

| Router | Endpoints | Owner |
|--------|-----------|-------|
| Health | `GET /health` | M2 |
| Auth | `POST /auth/login` · `/refresh` · `/logout` · `GET /auth/me` · `POST /auth/change-password` | M2 |
| Users | `GET/POST /users` · `GET/PATCH /users/{id}` · `/role` · `/reset-password` · `/status` | M2 |
| Groups | `POST /groups` · `GET /groups/me` · `/members` · `DELETE /members/{userId}` · `GET /groups/{id}` | M2 |
| Jobs | `GET /jobs/{id}` | M2 |
| Abstracts | `POST /abstracts` · `/import` · `GET /abstracts` · `GET/PATCH /abstracts/{id}` · `/reprocess` · `DELETE` | M3 |
| Proposals | `POST /proposals` · `GET /proposals` · `GET/PATCH /proposals/{id}` · `/analyze` · `/final-scope` | M3 |
| Quotas | `GET /quotas` · `PUT /quotas/{year}` · `GET /quotas/status` | M3 |
| Settings | `GET /settings` · `PUT /settings` | M3 |
| Reports | `GET /proposals/{id}/report` · `/suggestions` · `PATCH /suggestions/{sid}` | M1 |

> Interactive docs available at `http://localhost:8000/docs` when running locally.

---

## Background Jobs

The worker (`backend/app/worker/runner.py`) polls the `jobs` table and dispatches:

| Job Type | Triggered by | Handler (M1) |
|----------|-------------|-------------|
| `process_abstract` | Admin imports a past project | Extracts fields + embeddings via AI |
| `analyze_proposal` | Student clicks Analyze | Runs hybrid search + comparison + scoring + suggestions |

Poll the job status at `GET /jobs/{id}`.

---

## AI Pipeline (M1)

```
Student uploads proposal
        ↓
text_extract (ingestion)
        ↓
extract_idea_profile  ← idea_profile.md prompt
        ↓
hybrid_search  ← BGE-M3 embeddings + pgvector + keyword
        ↓
compare_features  ← feature_comparison.md prompt
        ↓
scoring  ← weights from settings table → score + risk band
        ↓
category & SDG suggestion  ← category_sdg_suggestion.md prompt
        ↓
feature_suggestions  ← feature_suggestions.md prompt
        ↓
Analysis + SimilarMatch + Suggestion rows saved to DB
        ↓
Student views ReadinessReport
```

**LLM provider** is selected by `LLM_PROVIDER` env var:
- `mock` — no API key needed, returns hardcoded stubs (use for local dev)
- `claude` — calls Anthropic Claude API (requires `CLAUDE_API_KEY`)

Every LLM response is JSON-validated with retry (up to 3 attempts) in `ai/validation.py`.

---

## Database Models at a Glance

```
users ──< refresh_tokens
users ──< group_members >── groups
users ──< audit_logs

import_batches ──< past_projects ──< past_project_features
past_projects ──< past_project_sdgs >── sdgs
past_projects.category_id → categories

groups ──< proposals ──< documents
proposals ──< analyses ──< similar_matches → past_projects
analyses ──< suggestions
proposals ──< final_scopes ──< final_scope_sdgs >── sdgs

categories ──< quotas
jobs (polled by worker)
settings (key-value)
llm_usage (per-call token log)
```

---

## How to Run (Local Dev)

```bash
# 1. Clone
git clone <repo-url>
cd ideascope

# 2. Set up environment
cp .env.example .env
# Open .env and set:
#   POSTGRES_PASSWORD, JWT_SECRET, MAIN_ADMIN_PASSWORD
#   LLM_PROVIDER=mock   ← no Claude key needed for dev

# 3. Start everything
docker compose up --build

# API → http://localhost:8000
# Docs → http://localhost:8000/docs

# 4. Seed initial data (run once after first startup)
docker compose exec api python backend/scripts/setup_initial_data.py

# 5. Frontend (separate terminal)
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

---

## Branch Rules

| Rule | Detail |
|------|--------|
| Feature branches | `feature/<your-name>/<short-description>` |
| Bug fixes | `fix/<short-description>` |
| `main` is protected | No direct pushes — PR required |
| PR review | At least 1 reviewer from CODEOWNERS for the changed paths |
| Shared code | `core/`, shared models — 2 reviewers required |
| Commit messages | `feat:`, `fix:`, `chore:`, `docs:` prefixes |

---

## Environment Variables

All config is read from `.env` via `backend/app/core/config.py`. See `.env.example` for the full list. **Never commit `.env` to git.**

Key variables:

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | PostgreSQL connection string |
| `JWT_SECRET` | Signing key for access/refresh tokens |
| `LLM_PROVIDER` | `mock` (dev) or `claude` (prod) |
| `CLAUDE_API_KEY` | Required only when `LLM_PROVIDER=claude` |
| `EMBEDDING_MODEL` | HuggingFace model name (default: `BAAI/bge-m3`) |
| `MAIN_ADMIN_EMAIL` | Bootstrapped admin account email |
| `MAIN_ADMIN_PASSWORD` | Bootstrapped admin account password |

---

## Running Tests

```bash
# Inside the api container or with venv active
cd backend
pytest tests/ -v
```

| Test File | Owner | Covers |
|-----------|-------|--------|
| `test_security.py` | M2 | JWT creation, bcrypt, token decode |
| `test_roles.py` | M2 | Role-based access control |
| `test_quota.py` | M3 | Quota logic, increment, status |
| `test_ingestion.py` | M3 | Excel import, dedup, normalize |
| `test_scoring.py` | M1 | Similarity scoring, risk bands |

---

## Deployment

See `deploy/README_DEPLOY.md` for the full Contabo VPS guide (Nginx, Let's Encrypt, SSH-key only, firewall, daily DB backup). Owned by **M1**.


---

## Environment & Development Setup

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Git](https://git-scm.com/)
- [Node.js 24 LTS](https://nodejs.org/) (managed via `nvm`: run `nvm use 24` or `nvm install 24`)

### Configuration
Create a local `.env` file from the example:
```bash
cp .env.example .env
```
Update `.env` with your local development credentials.

> [!IMPORTANT]
> `.env` contains local environment secrets and is **never committed** to git. Conversely, `frontend/package-lock.json` **must be committed** to ensure reproducible frontend builds.

### Running Services
- **Daily development (Database only):**
  ```bash
  docker compose up -d db
  ```
- **Full stack (when application code is implemented):**
  ```bash
  docker compose --profile app up --build
  ```

### Service URLs & Ports
- **Frontend UI:** [http://localhost:5173](http://localhost:5173) (Port 5173)
- **API Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs) (Port 8000)
- **PostgreSQL Database:** `localhost:5433` (Host port 5433 maps to container port 5432)

### Useful Docker Commands
- View database logs:
  ```bash
  docker compose logs -f db
  ```
- Stop running containers:
  ```bash
  docker compose down
  ```
- Reset database and clear volumes:
  ```bash
  docker compose down -v
  ```

### Tooling & Code Quality Commands
- **Backend Linting:**
  ```bash
  ruff check backend
  ```
- **Frontend Linting:**
  ```bash
  cd frontend && npm run lint
  ```
- **Frontend Formatting:**
  ```bash
  cd frontend && npm run format
  ```
