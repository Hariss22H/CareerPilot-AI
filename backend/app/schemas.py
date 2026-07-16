from pydantic import BaseModel, Field, field_validator


class ResumeRewrite(BaseModel):
    before: str
    after: str


class LearningRoadmap(BaseModel):
    week1: list[str] = Field(default_factory=list)
    week2: list[str] = Field(default_factory=list)
    week3: list[str] = Field(default_factory=list)
    week4: list[str] = Field(default_factory=list)


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


class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    error_code: str

