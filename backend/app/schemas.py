from pydantic import BaseModel, Field


class HiringRules(BaseModel):
    mandatory_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    min_experience_years: int | None = None
    required_seniority: str | None = None
    min_education: str | None = None
    location: str | None = None
    language: str | None = None
    max_salary: int | None = None
    employment_type: str | None = None
    work_authorization: str | None = None
    industry: str | None = None


class JobInput(BaseModel):
    title: str = Field(..., description="عنوان الوظيفة")
    description: str = Field(..., description="وصف الوظيفة")
    required_skills: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    experience_level: str = ""
    domain: str = ""
    hiring_rules: HiringRules | None = None


class CandidateMatchResponse(BaseModel):
    job_title: str
    match_percentage: float
    ranking: int | None = None
    similarity: float
    skill_score: float
    title_score: float = 0.0
    missing_skills: list[str]
    matched_skills: list[str] = Field(default_factory=list)
    evidence: dict[str, str] = Field(default_factory=dict)
    skill_levels: dict[str, str] = Field(default_factory=dict)
    missing_skills_by_group: dict[str, list[str]] = Field(default_factory=dict)
    reason: str = ""
    confidence_score: float = 0.0
    match_level: str = "Medium"
    feedback: str = ""
    recommendation: str = ""
    score_breakdown: dict[str, float] = Field(default_factory=dict)
    logs: list[str]
    rule_status: str = "PASSED"
    rule_reasons: list[str] = Field(default_factory=list)



class CandidateProfile(BaseModel):
    name: str
    headline: str
    skills: list[str] = Field(default_factory=list)
    summary: str = ""


class JobMatchRequest(BaseModel):
    job: JobInput
    candidate: CandidateProfile


class TopMatchesRequest(BaseModel):
    candidate: CandidateProfile
    jobs: list[JobInput] = Field(default_factory=list)


class TopMatchesResponse(BaseModel):
    candidate_name: str
    total_jobs: int
    matches: list[CandidateMatchResponse]


class ProfileSummary(BaseModel):
    candidate_level: str
    main_domain: str
    inferred_headline: str
    short_description: str
    key_skills: list[str] = Field(default_factory=list)
    years_of_experience: int = 0


class RoleAnalysisItem(BaseModel):
    role_name: str
    match_level: str
    confidence_score: float
    reason: str
    matched_skills: list[str] = Field(default_factory=list)
    evidence: dict[str, str] = Field(default_factory=dict)
    skill_levels: dict[str, str] = Field(default_factory=dict)
    missing_skills: list[str] = Field(default_factory=list)
    missing_skills_by_group: dict[str, list[str]] = Field(default_factory=dict)


class CareerGrowthPlan(BaseModel):
    next_learning_priorities: list[str] = Field(default_factory=list)
    roadmap_steps: list[str] = Field(default_factory=list)


class StrengthWeaknessReport(BaseModel):
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)


class FullCvAnalysisResponse(BaseModel):
    profile_summary: ProfileSummary
    top_roles: list[RoleAnalysisItem] = Field(default_factory=list)
    career_growth_plan: CareerGrowthPlan
    strengths_vs_weaknesses: StrengthWeaknessReport
    analysis_logs: list[str] = Field(default_factory=list)


class CandidateComparisonRequest(BaseModel):
    job: JobInput
    candidates: list[CandidateProfile] = Field(default_factory=list)


class CandidateComparisonResponse(BaseModel):
    job_title: str
    ranking: list[CandidateMatchResponse]


class InterviewMessage(BaseModel):
    session_id: str
    message: str


class InterviewStartRequest(BaseModel):
    application_id: str


class InterviewStartResponse(BaseModel):
    session_id: str
    application_id: str
    job_title: str
    candidate_name: str
    status: str
    total_questions: int
    current_question_index: int
    current_question: str | None = None


class InterviewAnswerRequest(BaseModel):
    session_id: str
    answer: str


class InterviewAnswerResponse(BaseModel):
    session_id: str
    status: str
    current_question_index: int
    next_question: str | None = None
    answer_score: float
    answer_feedback: str
    is_completed: bool
    final_score: float | None = None
    final_recommendation: str | None = None


class InterviewTurn(BaseModel):
    question_index: int
    question_text: str
    candidate_answer: str
    answer_score: float
    feedback: str


class InterviewReportResponse(BaseModel):
    session_id: str
    application_id: str
    job_title: str
    candidate_name: str
    status: str
    total_questions: int
    answered_questions: int
    average_score: float
    recommendation: str
    overall_score: float = 0.0
    level: str = ""
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    hire_recommendation: str = ""
    started_at: str
    completed_at: str | None = None
    turns: list[InterviewTurn] = Field(default_factory=list)


class PostedJob(BaseModel):
    id: str
    title: str
    description: str
    required_skills: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    experience_level: str = ""
    domain: str = ""
    hiring_rules: HiringRules | None = None
    created_at: str



class PostedJobsResponse(BaseModel):
    jobs: list[PostedJob] = Field(default_factory=list)


class PostedJobDetails(BaseModel):
    job: PostedJob
    applicants_count: int


class JobApplication(BaseModel):
    id: str
    job_id: str
    candidate_name: str
    candidate_headline: str
    candidate_skills: list[str] = Field(default_factory=list)
    match_score: float
    missing_skills: list[str] = Field(default_factory=list)
    score_breakdown: dict[str, float] = Field(default_factory=dict)
    feedback: str = ""
    interview_status: str | None = None
    interview_score: float | None = None
    created_at: str


class CompanyDashboardJob(BaseModel):
    job: PostedJob
    applicants: list[JobApplication] = Field(default_factory=list)


class CompanyDashboardResponse(BaseModel):
    total_jobs: int
    total_applications: int
    jobs: list[CompanyDashboardJob] = Field(default_factory=list)


class AuthUserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    company_name: str = ""
    is_active: bool = True
    created_at: str
    updated_at: str
    last_login_at: str | None = None


class AuthSessionResponse(BaseModel):
    user: AuthUserResponse
    access_token: str
    token_type: str = "bearer"
    expires_at: str


class AuthRegisterRequest(BaseModel):
    full_name: str
    email: str
    password: str
    role: str = "candidate"
    company_name: str = ""


class AuthLoginRequest(BaseModel):
    email: str
    password: str
