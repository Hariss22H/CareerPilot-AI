from pydantic import BaseModel, Field, field_validator


class ResumeRewrite(BaseModel):
    before: str
    after: str


class LearningRoadmap(BaseModel):
    week1: list[str] = Field(default_factory=list)
    week2: list[str] = Field(default_factory=list)
    week3: list[str] = Field(default_factory=list)
    week4: list[str] = Field(default_factory=list)


class JobMatch(BaseModel):
    overall_match_score: int = Field(ge=0, le=100)
    skill_match: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    required_keywords_missing: list[str] = Field(default_factory=list)
    experience_gap: str
    education_gap: str
    recommended_improvements: list[str] = Field(default_factory=list)


class Analysis(BaseModel):
    ats_score: int = Field(ge=0, le=100)
    ats_reason: str
    strengths: list[str]
    weaknesses: list[str]
    matched_skills: list[str]
    missing_skills: list[str]
    resume_suggestions: list[str]
    rejection_reason: str
    resume_rewrite: ResumeRewrite
    learning_roadmap: LearningRoadmap
    interview_questions: list[str]
    job_match: JobMatch | None = None

    @field_validator(
        "ats_reason",
        "rejection_reason",
        "strengths",
        "weaknesses",
        "matched_skills",
        "missing_skills",
        "resume_suggestions",
        "interview_questions",
    )
    @classmethod
    def require_content(cls, value):
        if not value or (isinstance(value, str) and not value.strip()):
            raise ValueError("Analysis field cannot be empty")
        return value


class AnalysisResponse(BaseModel):
    success: bool = True
    analysis: Analysis
    report_id: str | None = None


class CoverLetterRequest(BaseModel):
    report_id: str


class CoverLetterResponse(BaseModel):
    success: bool = True
    report_id: str
    cover_letter: str


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    session_id: str | None = None


class ChatResponse(BaseModel):
    success: bool = True
    session_id: str
    message: str


class ChatHistoryItem(BaseModel):
    role: str
    message: str
    created_at: str


class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    error_code: str


class RegisterRequest(BaseModel):
    full_name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: str
    full_name: str
    email: str
    created_at: str


class AuthResponse(BaseModel):
    success: bool = True
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class HistoryItem(BaseModel):
    id: str
    resume_name: str
    target_role: str
    ats_score: int | None = None
    created_at: str
    has_job_description: bool = False
