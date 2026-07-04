from typing import Annotated, Literal

from pydantic import BaseModel, Field


RequiredText = Annotated[str, Field(min_length=1, max_length=120)]
OptionalText = Annotated[str, Field(max_length=120)]
ListText = Annotated[str, Field(min_length=1, max_length=80)]


class StudentProfileRequest(BaseModel):
    education_level: RequiredText
    branch: RequiredText
    specialization: OptionalText | None = None
    cgpa: float = Field(ge=0, le=10)
    class_10_percentage: float | None = Field(default=None, ge=0, le=100)
    class_12_percentage: float | None = Field(default=None, ge=0, le=100)
    total_certifications: int = Field(default=0, ge=0, le=500)
    total_projects: int = Field(default=0, ge=0, le=500)
    internship_count: int = Field(default=0, ge=0, le=100)
    hackathons: int = Field(default=0, ge=0, le=500)
    leetcode_questions: int = Field(default=0, ge=0, le=100000)
    github_repositories: int = Field(default=0, ge=0, le=10000)
    expected_salary_lpa: float | None = Field(default=None, ge=0, le=1000)
    preferred_work_mode: OptionalText | None = None
    career_goal: OptionalText | None = None
    user_type: Literal["Student", "Fresher", "Experienced", "Career Switcher"] = "Student"
    age: int | None = Field(default=None, ge=13, le=80)
    years_experience: float | None = Field(default=None, ge=0, le=60)
    current_role: OptionalText | None = None
    location_preference: OptionalText | None = "India"
    certifications: list[ListText] = Field(default_factory=list, max_length=30)
    skills: list[ListText] = Field(default_factory=list, max_length=50)
    interests: list[ListText] = Field(default_factory=list, max_length=30)


class RoadmapStep(BaseModel):
    title: str
    actions: list[str]


class CareerRecommendation(BaseModel):
    career: str
    match_score: float = Field(ge=0, le=1)
    matched_skills: list[str]
    missing_skills: list[str]
    roadmap: list[RoadmapStep]


class RecommendationResponse(BaseModel):
    recommendations: list[CareerRecommendation]


class ChatMessage(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str = Field(min_length=1, max_length=1200)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1200)
    profile: StudentProfileRequest | None = None
    recommendations: list[CareerRecommendation] = Field(default_factory=list)
    history: list[ChatMessage] = Field(default_factory=list, max_length=20)


class ChatResponse(BaseModel):
    answer: str
