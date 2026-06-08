"""Phase 5 — Market Intelligence routes."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from backend.app.services.auth_service import require_current_user

router = APIRouter(dependencies=[Depends(require_current_user)])


class RecommendationRequest(BaseModel):
    candidate_skills: list[str] = Field(default_factory=list)
    limit: int = 10


@router.get("/trends/skills")
def skill_trends() -> dict:
    from ai_engine.services.market_intelligence import market_intelligence_service
    return market_intelligence_service.get_skill_trends()

@router.get("/trends/hiring")
def hiring_trends() -> dict:
    from ai_engine.services.market_intelligence import market_intelligence_service
    return market_intelligence_service.get_hiring_trends()

@router.get("/trends/technology")
def technology_trends() -> dict:
    from ai_engine.services.market_intelligence import market_intelligence_service
    return market_intelligence_service.get_technology_trends()

@router.get("/trends/domains")
def domain_distribution() -> dict:
    from ai_engine.services.market_intelligence import market_intelligence_service
    return market_intelligence_service.get_domain_distribution()

@router.post("/recommendations/jobs")
def job_recommendations(req: RecommendationRequest) -> dict:
    from ai_engine.services.recommendation_service import recommendation_service
    return recommendation_service.recommend_jobs(req.candidate_skills, req.limit)

@router.post("/recommendations/career-paths")
def career_paths(req: RecommendationRequest) -> dict:
    from ai_engine.services.recommendation_service import recommendation_service
    return recommendation_service.suggest_career_paths(req.candidate_skills)

@router.post("/recommendations/skills-to-learn")
def skills_to_learn(req: RecommendationRequest) -> dict:
    from ai_engine.services.recommendation_service import recommendation_service
    return recommendation_service.prioritize_skills_to_learn(req.candidate_skills)

@router.get("/forecast/skills")
def forecast_skills() -> dict:
    from ai_engine.services.forecasting_service import forecasting_service
    return forecasting_service.forecast_emerging_skills()

@router.get("/forecast/demand")
def forecast_demand() -> dict:
    from ai_engine.services.forecasting_service import forecasting_service
    return forecasting_service.forecast_hiring_demand()

@router.get("/forecast/industry")
def forecast_industry() -> dict:
    from ai_engine.services.forecasting_service import forecasting_service
    return forecasting_service.detect_industry_shifts()
