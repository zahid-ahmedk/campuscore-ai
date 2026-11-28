# QUEST IT Portal

Student records, fee management and academic-standing monitoring for the **Department of Information Technology, Quaid-e-Awam University of Engineering, Science & Technology (QUEST), Nawabshah**.

| Role | Can do |
| --- | --- |
| Student | View own record, dues and payment history; submit challan receipts; ask the assistant about own standing |
| Clerk | Manage students, raise fees, verify or reject challan receipts |
| Chairman | Department dashboard, risk monitoring, fee oversight |
| Administrator | Departments, staff accounts, audit log, model re-scoring |

## Features

- **Fee management and challans.** Dues per semester and category, payment history, and a Pending / Verified / Rejected workflow. Students submit an alphanumeric **Challan No.**, a fee category (Semester Tuition, Examination, Subject Improvement / Repeat, Hostel, Transport, Clearance / Degree, or **Custom** with free text) and a receipt in `.pdf`, `.jpg`, `.jpeg`, `.png` or `.webp`. Uploads are checked for extension, size (5 MB) and file signature; receipts open in an in-app preview with download. Duplicate challan numbers and overpayments are rejected. A due's paid amount is always derived from *verified* payments.
- **Role-based access.** JWT authentication; every endpoint checks the caller's role, and staff only see their own department. Students can only reach their own data.
- **Assistant.** Answers are computed from live database queries (overview, high-risk students, fee totals, student lookup). With `OPENAI_API_KEY` set, a language model chooses among the same role-filtered tools and phrases the result; without it, a rule-based router is used. Students can only call their own-data tool.
- **Academic standing model.** A Random Forest on attendance, midterm %, sessional % and fee clearance. It is bootstrapped from synthetic data until real outcome records exist, so treat it as a screening aid, not a validated prediction (see `backend/ml_engine.py`).
- **Scale.** Server-side pagination (max 100 rows), composite indexes, SQL aggregates for dashboards, chunked vectorised re-scoring, PostgreSQL-ready connection pooling.

## Measured performance

`backend/bench.py` seeds a scratch database and times the hot endpoints. Result on 100,000 students (SQLite, in-process client, one user, sandbox machine):

| Operation | Median |
| --- | --- |
| Student list page (25 rows), any page | 8-9 ms |
| Filter by batch and risk | 11 ms |
| Sort by CGPA | 17 ms |
| Dashboard summary (aggregates) | 64 ms |
| Fee list, status filter | 37 ms |
| Name or roll search | 103 ms |
| Re-score all 100,004 students | 4.5 s |

This is single-user latency, not a concurrent load test. For production use PostgreSQL (`DATABASE_URL`) and run several uvicorn/gunicorn workers.

## Run locally

```bash
# Backend
cd backend
python -m venv .venv && .venv\Scripts\activate      # Windows
pip install -r requirements.txt
copy .env.example .env                               # then set SECRET_KEY
python seed.py                                       # demo data
uvicorn main:app --reload

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

Or double-click `start_campuscore.bat` after the first-time setup. Open http://localhost:3000.

Load-test data: `python seed.py --students 100000` (synthetic, other departments). Tests: `cd backend && python -m pytest`.

### Demo accounts (development only, password `Quest@2026`)

`admin@quest-portal.local` · `chairman@quest-portal.local` · `clerk@quest-portal.local` · `21it95@quest-portal.local`

Delete or change these before any real deployment.

## Configuration

| Variable | Purpose |
| --- | --- |
| `SECRET_KEY` | JWT signing key (required in production) |
| `DATABASE_URL` | Default SQLite; use `postgresql+psycopg2://...` for production |
| `CORS_ORIGINS` | Allowed web origins |
| `ROLL_NO_PATTERN` | Roll number regex, default `^\d{2}[A-Z]{2,4}-\d{1,3}$` (e.g. `21IT-95`) |
| `OPENAI_API_KEY` | Optional, enables the language-model assistant |
| `NEXT_PUBLIC_API_URL` | Frontend API base, default `http://127.0.0.1:8000/api` |

## Layout

```
backend/   FastAPI: routers/, services/, models.py, security.py, storage.py, ml_engine.py, tests/
frontend/  Next.js (App Router): app/(portal)/, components/, lib/
```
