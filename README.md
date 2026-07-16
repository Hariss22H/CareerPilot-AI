# AI SkillBridge

AI SkillBridge is a stateless career-readiness MVP. A student uploads a PDF resume and enters a target role; the application extracts the resume text, makes one structured AI analysis request, and renders an actionable career report.

## Run locally

The commands below are for PowerShell. If your terminal shows `MINGW64` or `Git Bash`, use the Git Bash commands in the next section instead.

### Backend

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload --port 8000
```

OpenAI is the default provider. Add your key to `backend/.env` for live analysis:

```env
AI_PROVIDER=openai
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o-mini
```

If no provider key is configured, the backend returns a deterministic development report so the end-to-end UI can still be tested. Gemini remains available by setting `AI_PROVIDER=gemini` and configuring `GEMINI_API_KEY`.

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Set `VITE_API_URL` if the backend is not running at `http://localhost:8000`.

### Git Bash

From Git Bash, use Unix-style paths and commands:

```bash
cd /e/AI_skillbridge/backend
python -m venv .venv
source .venv/Scripts/activate
python -m pip install -r requirements.txt
cp .env.example .env
python -m uvicorn app.main:app --reload --port 8000
```

In a second Git Bash terminal:

```bash
cd /e/AI_skillbridge/frontend
npm install
npm run dev
```

## API

- `GET /api/health` returns the service health status.
- `POST /api/analyze-resume` accepts multipart fields `resume` and `job_role` and returns the validated report schema.

The backend allows only the configured frontend origin through CORS. In production, set `FRONTEND_URL` to the deployed frontend URL and provide `GEMINI_API_KEY` through the hosting provider's secret settings.

## MVP boundaries

The app intentionally does not include authentication, persistence, resume history, job scraping, a resume builder, external learning links, or interactive mock interviews. Resumes are processed in memory and are not stored.
