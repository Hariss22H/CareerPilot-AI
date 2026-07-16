import logging

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .ai_service import analyze_resume
from .config import get_settings
from .resume_parser import ResumeParseError, extract_resume_text
from .schemas import AnalysisResponse, ErrorResponse

settings = get_settings()
logging.basicConfig(level=settings.log_level)
app = FastAPI(title="AI SkillBridge API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_error_handler(_request: Request, exc: HTTPException):
    detail = exc.detail if isinstance(exc.detail, dict) else {
        "success": False,
        "message": str(exc.detail),
        "error_code": "REQUEST_FAILED",
    }
    return JSONResponse(status_code=exc.status_code, content=detail)


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "healthy"}


@app.post("/api/analyze-resume", response_model=AnalysisResponse, responses={400: {"model": ErrorResponse}, 422: {"model": ErrorResponse}, 503: {"model": ErrorResponse}})
async def analyze_endpoint(resume: UploadFile | None = File(default=None), job_role: str = Form(default="")):
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
    try:
        analysis = await analyze_resume(text, role, settings)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail={"success": False, "message": str(exc), "error_code": "AI_UNAVAILABLE"}) from exc
    return {"success": True, "analysis": analysis}
