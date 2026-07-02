from pydantic import BaseModel, Field


class StudentProfileRequest(BaseModel):
    education_level: str
    branch: str
    specialization: str | None = None
    cgpa: float = Field(ge=0, le=10)
    class_10_percentage: float | None = Field(default=None, ge=0, le=100)
    class_12_percentage: float | None = Field(default=None, ge=0, le=100)
    total_certifications: int = Field(default=0, ge=0)
    total_projects: int = Field(default=0, ge=0)
    internship_count: int = Field(default=0, ge=0)
    hackathons: int = Field(default=0, ge=0)
    leetcode_questions: int = Field(default=0, ge=0)
    github_repositories: int = Field(default=0, ge=0)
    expected_salary_lpa: float | None = Field(default=None, ge=0)
    preferred_work_mode: str | None = None
    career_goal: str | None = None
    certifications: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    interests: list[str] = Field(default_factory=list)


class RoadmapStep(BaseModel):
    title: str
    actions: list[str]


class CareerRecommendation(BaseModel):
    career: str
    confidence: float
    matched_skills: list[str]
    missing_skills: list[str]
    roadmap: list[RoadmapStep]


class RecommendationResponse(BaseModel):
    recommendations: list[CareerRecommendation]


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    profile: StudentProfileRequest | None = None
    recommendations: list[CareerRecommendation] = Field(default_factory=list)
    history: list[ChatMessage] = Field(default_factory=list)


class ChatResponse(BaseModel):
    answer: str
