# AI SkillBridge

AI SkillBridge is an AI-powered career readiness platform for students and early-career candidates. It compares a resume with a target role and optional job description, then produces a practical plan for becoming job-ready.

The private Career Workspace includes saved reports, job-description matching, cover letters, a four-week learning roadmap, interview preparation, PDF exports, and a context-aware Career Coach.

## Live Demo

Try the deployed application:

**[Open AI SkillBridge](https://career-pilot-ai-opal.vercel.app/)**

## Features

### Resume Intelligence

- PDF resume upload and text extraction
- ATS compatibility score and reasoning
- Resume strengths, weaknesses, matched skills, and priority gaps
- Recruiter-style rejection simulation
- Actionable resume improvement suggestions
- Fact-preserving Before/After bullet rewrite
- Four-week learning roadmap
- Technical and behavioral interview questions

### Job Description Intelligence

- Paste a job description or upload a PDF/TXT file
- Resume-to-job semantic match score
- Matched and missing requirements
- Missing keywords, experience gaps, and education gaps
- Improvements aligned to employer requirements

### Career Workspace

- JWT authentication and user-scoped data
- MongoDB persistence for users, reports, and conversations
- Saved analysis history and report reopening
- Cover-letter generation from saved reports
- PDF report export
- Career Coach conversation history

### AI and Platform Engineering

- OpenAI support with Gemini as an alternative provider
- Deterministic development fallback without an AI key
- LangChain isolated to Career Coach and retrieval workflows
- Direct AI service calls for resume analysis and cover letters
- Replaceable retrieval boundary for job-description context
- Coach request rate limiting
- Docker Compose and GitHub Actions CI

## Architecture

```text
React + Vite frontend
          |
          | HTTP / JSON
          v
FastAPI backend
  |       |        |
  |       |        +-- Resume and JD PDF/TXT parsers
  |       +----------- Career Coach -> LangChain -> retrieval boundary
  +------------------- Direct AI service -> OpenAI or Gemini
          |
          v
MongoDB: users, reports, sessions, messages
```

LangChain is deliberately not used across the entire application. Resume analysis and cover-letter generation use direct AI service calls. LangChain is limited to the Career Coach, where prompt composition, conversation history, and retrieval context are useful.

## Project Structure

```text
AI_skillbridge/
├── backend/app/
│   ├── ai_service.py       # Resume analysis and cover letters
│   ├── auth.py             # Password hashing and JWT handling
│   ├── career_coach.py     # LangChain Career Coach
│   ├── config.py           # Environment-backed settings
│   ├── job_description.py  # Job-description extraction
│   ├── main.py             # FastAPI routes and lifecycle
│   ├── rag.py              # Retrieval boundary
│   ├── rate_limit.py       # In-memory request limiter
│   ├── report_export.py    # PDF report generation
│   ├── resume_parser.py    # Resume PDF extraction
│   ├── schemas.py          # Pydantic models
│   └── storage.py          # MongoDB and in-memory stores
├── backend/tests/
├── frontend/src/main.jsx  # React application
├── frontend/src/styles.css
├── .github/workflows/ci.yml
├── docker-compose.yml
└── README.md
```

## Requirements

- Python 3.11 or newer
- Node.js 22 or newer and npm
- MongoDB or MongoDB Atlas for persistence
- Docker Desktop for the Compose workflow
- OpenAI or Gemini API key for live AI responses

The application can run without MongoDB using an in-memory store, and without an AI key using a deterministic development fallback.

## Local Development

### Backend

Run in PowerShell:

```powershell
cd E:\AI_skillbridge\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Configure `backend/.env` for live analysis:

```env
AI_PROVIDER=openai
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o-mini
```

Start the first terminal:

```powershell
python -m uvicorn app.main:app --reload --port 8000
```

### Frontend

Open a second terminal:

```powershell
cd E:\AI_skillbridge\frontend
npm install
Copy-Item .env.example .env
npm run dev
```

Open `http://localhost:5173`. The frontend defaults to `http://localhost:8000`; override it with `VITE_API_URL` in `frontend/.env` if necessary.

Backend URLs:

- API: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Git Bash

Backend:

```bash
cd /e/AI_skillbridge/backend
python -m venv .venv
source .venv/Scripts/activate
python -m pip install -r requirements.txt
cp .env.example .env
python -m uvicorn app.main:app --reload --port 8000
```

Frontend, in a second terminal:

```bash
cd /e/AI_skillbridge/frontend
npm install
cp .env.example .env
npm run dev
```

## Docker

Run Docker Compose from the repository root, where `docker-compose.yml` is located:

```powershell
cd E:\AI_skillbridge
docker compose up --build
```

Services:

- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`
- MongoDB: internal Compose service at `mongodb://mongo:27017`

Stop the stack:

```powershell
docker compose down
```

Remove containers and the local MongoDB volume:

```powershell
docker compose down -v
```

The `-v` command permanently deletes local Docker database data. Compose reads AI credentials from `backend/.env` and points the backend to the bundled `mongo` service.

## Configuration

Backend settings are documented in [backend/.env.example](backend/.env.example):

| Variable | Purpose | Example |
| --- | --- | --- |
| `MONGODB_URI` | MongoDB connection string | `mongodb://localhost:27017` |
| `MONGODB_DATABASE` | Database name | `careerpilot` |
| `JWT_SECRET` | Access-token signing secret | long random value |
| `JWT_EXPIRE_MINUTES` | Access-token lifetime | `1440` |
| `AI_PROVIDER` | `openai` or `gemini` | `openai` |
| `OPENAI_API_KEY` | OpenAI credential | provider secret |
| `OPENAI_MODEL` | OpenAI model | `gpt-4o-mini` |
| `GEMINI_API_KEY` | Gemini credential | provider secret |
| `MODEL_NAME` | Gemini model | `gemini-2.0-flash` |
| `FRONTEND_URL` | Allowed CORS origin | `http://localhost:5173` |
| `MAX_FILE_SIZE` | Upload limit in bytes | `10485760` |
| `AI_TIMEOUT_SECONDS` | AI request timeout | `45` |
| `CHAT_MAX_TOKENS` | Coach output limit | `700` |
| `RATE_LIMIT_REQUESTS` | Requests per window | `30` |
| `RATE_LIMIT_WINDOW_SECONDS` | Rate-limit window | `60` |

Frontend settings are documented in [frontend/.env.example](frontend/.env.example): `VITE_API_URL`, `VITE_APP_NAME`, and `VITE_AUTH_TOKEN_KEY`.

### MongoDB Atlas

Set `MONGODB_URI` to the Atlas connection string for persistent cloud storage. URL-encode credentials inside the URI: `@` becomes `%40`, `#` becomes `%23`, `:` becomes `%3A`, and `/` becomes `%2F`. Keep the `@` separating credentials from the cluster hostname.

In Atlas, confirm that the cluster is running and add the development machine's public IP under **Network Access**. If `MONGODB_URI` is empty, the backend uses an in-memory store and data disappears when the server restarts. Connection failures return `503 DATABASE_UNAVAILABLE` rather than an internal traceback.

## API Reference

Protected endpoints require:

```http
Authorization: Bearer <access_token>
```

### System and Authentication

| Method | Endpoint | Description | Auth |
| --- | --- | --- | --- |
| `GET` | `/api/health` | Service health check | No |
| `POST` | `/api/auth/register` | Register and issue a JWT | No |
| `POST` | `/api/auth/login` | Authenticate and issue a JWT | No |
| `POST` | `/api/auth/logout` | Logout endpoint | Yes |
| `GET` | `/api/auth/profile` | Current user profile | Yes |

### Reports

| Method | Endpoint | Description | Auth |
| --- | --- | --- | --- |
| `POST` | `/api/analyze-resume` | Analyze resume and optional JD | Yes |
| `POST` | `/api/generate-cover-letter` | Generate from a saved report | Yes |
| `GET` | `/api/history` | List the user's reports | Yes |
| `GET` | `/api/history/{analysis_id}` | Load one report | Yes |
| `DELETE` | `/api/history/{analysis_id}` | Delete one report | Yes |
| `GET` | `/api/report/{analysis_id}/pdf` | Export a report as PDF | Yes |

`POST /api/analyze-resume` expects multipart form data:

- `resume`: required PDF file
- `job_role`: required target role
- `job_description`: optional pasted description
- `job_description_file`: optional PDF or TXT description

### Career Coach

| Method | Endpoint | Description | Auth |
| --- | --- | --- | --- |
| `POST` | `/api/chat` | Ask a context-aware career question | Yes |
| `GET` | `/api/chat/history?session_id={id}` | Load a coach session | Yes |

Example request:

```json
{
  "message": "Which skill gap should I prioritize this month?",
  "session_id": null
}
```

The first request creates a session. Reuse its returned `session_id` for follow-up messages.

## Testing

Backend syntax validation:

```powershell
cd E:\AI_skillbridge\backend
.\.venv\Scripts\Activate.ps1
python -m compileall -q app
```

Backend tests:

```powershell
python -m pytest -q
```

Frontend production build:

```powershell
cd E:\AI_skillbridge\frontend
npm run build
```

The GitHub Actions workflow in [.github/workflows/ci.yml](.github/workflows/ci.yml) runs backend compilation, backend tests, and the frontend build for pushes and pull requests.

## Production Notes

Before deployment:

1. Replace the development `JWT_SECRET` with a long random secret.
2. Store API keys and database credentials in a secret manager.
3. Never commit `.env` files; commit only `.env.example` files.
4. Restrict MongoDB Atlas Network Access to trusted IP ranges.
5. Set `FRONTEND_URL` to the exact production frontend origin.
6. Serve the frontend and API over HTTPS.
7. Review upload limits, retention, logging, and rate limits.
8. Use a managed or securely configured production MongoDB deployment.
9. Replace the process-local rate limiter with shared infrastructure before using multiple API replicas.
10. Put a reverse proxy or API gateway in front of the services for TLS termination and access logging.

Resume and job-description content is treated as untrusted input. AI prompts explicitly instruct providers not to follow instructions embedded inside uploaded documents.

## Implementation Status

| Phase | Scope | Status |
| --- | --- | --- |
| 1 | JWT, MongoDB persistence, report history, Career Workspace | Implemented |
| 2 | Job Description parsing, matching, and cover letters | Implemented |
| 3 | LangChain Career Coach and scoped conversation memory | Implemented |
| 4 | Retrieval boundary for job-description context | Implemented |
| 5 | PDF export, rate limiting, Docker, CI, and tests | Implemented |

The existing clean UI is preserved while adding reports, cover letters, roadmap progress, and the Career Coach.

## License

No license has been specified yet. Add a `LICENSE` file before distributing this project publicly or accepting external contributions.
