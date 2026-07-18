import logging
import re
from contextlib import asynccontextmanager
from datetime import datetime

import jwt
from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordBearer
from pymongo.errors import PyMongoError

from .ai_service import analyze_resume, generate_cover_letter
from .auth import create_access_token, decode_access_token, hash_password, verify_password
from .config import get_settings
from .job_description import JobDescriptionError, extract_job_description
from .career_coach import CareerCoach
from .rate_limit import enforce_rate_limit
from .report_export import build_pdf
from .resume_parser import ResumeParseError, extract_resume_text
from .schemas import Analysis, AnalysisResponse, AuthResponse, ChatHistoryItem, ChatRequest, ChatResponse, CoverLetterRequest, CoverLetterResponse, ErrorResponse, HistoryItem, LoginRequest, RegisterRequest, UserResponse
from .storage import build_store, serialize_report

settings = get_settings()
logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.store = build_store(settings)
    yield
    await app.state.store.close()


app = FastAPI(title="CareerPilot AI API", version="2.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_error_handler(_request: Request, exc: HTTPException):
    detail = exc.detail if isinstance(exc.detail, dict) else {"success": False, "message": str(exc.detail), "error_code": "REQUEST_FAILED"}
    return JSONResponse(status_code=exc.status_code, content=detail, headers=exc.headers)


@app.exception_handler(PyMongoError)
async def database_error_handler(_request: Request, exc: PyMongoError):
    logger.error("MongoDB operation failed: %s", exc.__class__.__name__)
    return JSONResponse(
        status_code=503,
        content={
            "success": False,
            "message": "The database is temporarily unavailable. Check MongoDB Atlas network access and try again.",
            "error_code": "DATABASE_UNAVAILABLE",
        },
    )


def _user_response(user: dict) -> UserResponse:
    created_at = user.get("created_at")
    if isinstance(created_at, datetime):
        created_at = created_at.isoformat()
    return UserResponse(id=str(user["_id"]), full_name=user["full_name"], email=user["email"], created_at=str(created_at))


async def get_current_user(request: Request, token: str | None = Depends(oauth2_scheme)) -> dict:
    try:
        user = None
        if token:
            user_id = decode_access_token(token, settings)
            user = await request.app.state.store.get_user(user_id)
    except (jwt.InvalidTokenError, KeyError):
        user = None
    if user is None:
        raise HTTPException(status_code=401, headers={"WWW-Authenticate": "Bearer"}, detail={"success": False, "message": "Please log in to continue.", "error_code": "AUTH_REQUIRED"})
    return user


def _normalize_registration(data: RegisterRequest) -> tuple[str, str, str]:
    name = data.full_name.strip()
    email = data.email.strip().lower()
    if len(name) < 2 or len(name) > 100:
        raise HTTPException(status_code=400, detail={"success": False, "message": "Please enter your full name.", "error_code": "NAME_INVALID"})
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        raise HTTPException(status_code=400, detail={"success": False, "message": "Please enter a valid email address.", "error_code": "EMAIL_INVALID"})
    if len(data.password) < settings.password_min_length:
        raise HTTPException(status_code=400, detail={"success": False, "message": f"Password must be at least {settings.password_min_length} characters.", "error_code": "PASSWORD_WEAK"})
    return name, email, data.password


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "healthy"}


@app.post("/api/auth/register", response_model=AuthResponse)
async def register(data: RegisterRequest, request: Request):
    name, email, password = _normalize_registration(data)
    store = request.app.state.store
    if await store.find_user_by_email(email):
        raise HTTPException(status_code=409, detail={"success": False, "message": "An account with this email already exists.", "error_code": "EMAIL_EXISTS"})
    user = await store.create_user(name, email, hash_password(password))
    return {"access_token": create_access_token(user["_id"], settings), "user": _user_response(user)}


@app.post("/api/auth/login", response_model=AuthResponse)
async def login(data: LoginRequest, request: Request):
    email = data.email.strip().lower()
    user = await request.app.state.store.find_user_by_email(email)
    if user is None or not verify_password(data.password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, headers={"WWW-Authenticate": "Bearer"}, detail={"success": False, "message": "Email or password is incorrect.", "error_code": "INVALID_CREDENTIALS"})
    return {"access_token": create_access_token(user["_id"], settings), "user": _user_response(user)}


@app.post("/api/auth/logout")
async def logout(_user: dict = Depends(get_current_user)):
    return {"success": True, "message": "Logged out successfully."}


@app.get("/api/auth/profile", response_model=UserResponse)
async def profile(user: dict = Depends(get_current_user)):
    return _user_response(user)


@app.post("/api/analyze-resume", response_model=AnalysisResponse, responses={400: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 422: {"model": ErrorResponse}, 503: {"model": ErrorResponse}})
async def analyze_endpoint(
    request: Request,
    resume: UploadFile | None = File(default=None),
    job_role: str = Form(default=""),
    job_description: str = Form(default=""),
    job_description_file: UploadFile | None = File(default=None),
    user: dict = Depends(get_current_user),
    _limit=Depends(enforce_rate_limit),
):
    if resume is None:
        raise HTTPException(status_code=400, detail={"success": False, "message": "Please upload a PDF resume.", "error_code": "RESUME_REQUIRED"})
    role = job_role.strip()
    if not role or len(role) > 120 or not any(char.isalnum() for char in role):
        raise HTTPException(status_code=400, detail={"success": False, "message": "Please enter a valid target job role.", "error_code": "JOB_ROLE_INVALID"})
    if resume.content_type != "application/pdf" and not (resume.filename or "").lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail={"success": False, "message": "Only PDF files are supported.", "error_code": "UNSUPPORTED_FILE"})
    content = await resume.read()
    if not content or len(content) > settings.max_file_size:
        raise HTTPException(status_code=400, detail={"success": False, "message": "Please upload a PDF smaller than 10 MB.", "error_code": "FILE_SIZE_INVALID"})
    try:
        text = extract_resume_text(content, settings.min_resume_text_length)
    except ResumeParseError as exc:
        raise HTTPException(status_code=422, detail={"success": False, "message": str(exc), "error_code": "RESUME_PARSE_FAILED"}) from exc
    parsed_job_description = job_description.strip()
    if job_description_file is not None:
        jd_content = await job_description_file.read()
        if not jd_content or len(jd_content) > settings.max_file_size:
            raise HTTPException(status_code=400, detail={"success": False, "message": "Please upload a job description smaller than 10 MB.", "error_code": "JD_FILE_SIZE_INVALID"})
        try:
            uploaded_jd = extract_job_description(jd_content, job_description_file.filename or "job-description.txt", job_description_file.content_type or "")
        except JobDescriptionError as exc:
            raise HTTPException(status_code=422, detail={"success": False, "message": str(exc), "error_code": "JD_PARSE_FAILED"}) from exc
        parsed_job_description = f"{parsed_job_description}\n\n{uploaded_jd}".strip() if parsed_job_description else uploaded_jd
    if len(parsed_job_description) > 50000:
        raise HTTPException(status_code=400, detail={"success": False, "message": "Job description is too long. Please keep it under 50,000 characters.", "error_code": "JD_TOO_LONG"})
    try:
        analysis = await analyze_resume(text, role, settings, parsed_job_description)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail={"success": False, "message": str(exc), "error_code": "AI_UNAVAILABLE"}) from exc
    report = await request.app.state.store.save_analysis(user["_id"], resume.filename or "resume.pdf", role, analysis.model_dump(mode="json"), parsed_job_description)
    return {"success": True, "analysis": analysis, "report_id": report["_id"]}


@app.post("/api/generate-cover-letter", response_model=CoverLetterResponse)
async def cover_letter(data: CoverLetterRequest, request: Request, user: dict = Depends(get_current_user), _limit=Depends(enforce_rate_limit)):
    report = await request.app.state.store.get_analysis(user["_id"], data.report_id)
    if report is None:
        raise HTTPException(status_code=404, detail={"success": False, "message": "Career report not found.", "error_code": "REPORT_NOT_FOUND"})
    try:
        analysis = Analysis.model_validate(report["analysis"])
        letter = await generate_cover_letter(report["target_role"], report.get("job_description", ""), analysis, settings)
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=503, detail={"success": False, "message": str(exc), "error_code": "COVER_LETTER_UNAVAILABLE"}) from exc
    return {"success": True, "report_id": data.report_id, "cover_letter": letter}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(data: ChatRequest, request: Request, user: dict = Depends(get_current_user), _limit=Depends(enforce_rate_limit)):
    store = request.app.state.store
    session = await store.get_chat_session(user["_id"], data.session_id) if data.session_id else None
    if session is None:
        session = await store.create_chat_session(user["_id"])
    messages = await store.get_chat_messages(session["_id"])
    history = [{"role": item["role"], "content": item["message"]} for item in messages]
    reports = await store.list_analyses(user["_id"])
    latest = reports[0] if reports else {}
    personal_context = {"name": user["full_name"], "target_role": latest.get("target_role"), "analysis": latest.get("analysis", {})}
    job_documents = [item.get("job_description", "") for item in reports if item.get("job_description")]
    answer = await CareerCoach(settings).answer(data.message, personal_context, job_documents, history)
    await store.add_chat_message(session["_id"], "user", data.message)
    await store.add_chat_message(session["_id"], "assistant", answer)
    return {"success": True, "session_id": session["_id"], "message": answer}


@app.get("/api/chat/history", response_model=list[ChatHistoryItem])
async def chat_history(session_id: str, request: Request, user: dict = Depends(get_current_user)):
    session = await request.app.state.store.get_chat_session(user["_id"], session_id)
    if session is None:
        raise HTTPException(status_code=404, detail={"success": False, "message": "Chat session not found.", "error_code": "CHAT_NOT_FOUND"})
    messages = await request.app.state.store.get_chat_messages(session_id)
    return [{"role": item["role"], "message": item["message"], "created_at": item["created_at"].isoformat()} for item in messages]


@app.get("/api/report/{analysis_id}/pdf")
async def report_pdf(analysis_id: str, request: Request, user: dict = Depends(get_current_user)):
    report = await request.app.state.store.get_analysis(user["_id"], analysis_id)
    if report is None:
        raise HTTPException(status_code=404, detail={"success": False, "message": "Career report not found.", "error_code": "REPORT_NOT_FOUND"})
    try:
        pdf = build_pdf(report)
    except Exception as exc:
        logger.exception("PDF export failed: %s", type(exc).__name__)
        raise HTTPException(status_code=503, detail={"success": False, "message": "PDF export is temporarily unavailable.", "error_code": "PDF_EXPORT_UNAVAILABLE"}) from exc
    return StreamingResponse(pdf, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="career-report-{analysis_id}.pdf"'})


@app.get("/api/history", response_model=list[HistoryItem])
async def history(request: Request, user: dict = Depends(get_current_user)):
    return [serialize_report(report) for report in await request.app.state.store.list_analyses(user["_id"])]


@app.get("/api/history/{analysis_id}")
async def history_detail(analysis_id: str, request: Request, user: dict = Depends(get_current_user)):
    report = await request.app.state.store.get_analysis(user["_id"], analysis_id)
    if report is None:
        raise HTTPException(status_code=404, detail={"success": False, "message": "Career report not found.", "error_code": "REPORT_NOT_FOUND"})
    return serialize_report(report)


@app.delete("/api/history/{analysis_id}")
async def delete_history(analysis_id: str, request: Request, user: dict = Depends(get_current_user)):
    deleted = await request.app.state.store.delete_analysis(user["_id"], analysis_id)
    if not deleted:
        raise HTTPException(status_code=404, detail={"success": False, "message": "Career report not found.", "error_code": "REPORT_NOT_FOUND"})
    return {"success": True, "message": "Career report deleted."}
