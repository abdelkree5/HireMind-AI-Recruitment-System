from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

from backend.app.schemas import (
    CandidateComparisonResponse,
    CandidateMatchResponse,
    CandidateProfile,
    JobInput,
    TopMatchesResponse,
)
from backend.app.services.document_parser import extract_text_from_resume
from backend.app.services.feedback_service import build_feedback
from backend.app.services.cv_reasoning_engine import recommend_job_titles_from_cv_text
from backend.app.services.matching_service import matching_service
from backend.app.services.sample_data import SAMPLE_JOBS
from backend.app.services.skill_extractor import SkillExtractor


@dataclass
class AnalysisJobStore:
    queues: dict[str, asyncio.Queue] = field(default_factory=dict)
    results: dict[str, CandidateMatchResponse] = field(default_factory=dict)

    def create(self, job_id: str) -> asyncio.Queue:
        queue = asyncio.Queue()
        self.queues[job_id] = queue
        return queue

    def push(self, job_id: str, payload: dict) -> None:
        if job_id in self.queues:
            self.queues[job_id].put_nowait(payload)

    def done(self, job_id: str) -> None:
        self.push(job_id, {"type": "done"})


store = AnalysisJobStore()


@dataclass
class AnalysisState:
    job_id: str
    job: JobInput
    file_bytes: bytes
    filename: str


async def process_resume_job(state: AnalysisState) -> None:
    try:
        store.push(state.job_id, {"type": "log", "message": "Reading CV..."})
        text = extract_text_from_resume(state.file_bytes, state.filename)
        store.push(state.job_id, {"type": "log", "message": "Extracting skills..."})
        if not text.strip():
            raise ValueError("Uploaded file is empty.")

        skill_extractor = SkillExtractor()
        extracted_skills = skill_extractor.extract(text)
        store.push(state.job_id, {"type": "log", "message": f"Extracted skills: {', '.join(extracted_skills) or 'none'}"})
        store.push(state.job_id, {"type": "log", "message": "Calculating similarity..."})

        result = matching_service.analyze_resume(state.file_bytes, state.filename, state.job)
        store.push(state.job_id, {"type": "log", "message": "Ranking jobs..."})
        feedback = build_feedback(result.missing_skills)
        payload = result.model_dump()
        payload["feedback"] = feedback
        payload["type"] = "result"
        store.results[state.job_id] = result
        store.push(state.job_id, payload)
    except Exception as exc:  # pragma: no cover - clear message for API consumers
        store.push(state.job_id, {"type": "error", "message": str(exc)})
    finally:
        store.done(state.job_id)


def start_resume_analysis_job(job_id: str, file_bytes: bytes, filename: str, job: JobInput) -> asyncio.Queue:
    queue = store.create(job_id)
    state = AnalysisState(job_id=job_id, job=job, file_bytes=file_bytes, filename=filename)
    asyncio.create_task(process_resume_job(state))
    return queue


def analyze_resume_to_jobs(file_bytes: bytes, filename: str, job: JobInput) -> CandidateMatchResponse:
    return matching_service.analyze_resume(file_bytes, filename, job)


def match_candidate_to_job(job: JobInput, candidate: CandidateProfile) -> CandidateMatchResponse:
    candidate_text = f"{candidate.headline}. {candidate.summary}. {' '.join(candidate.skills)}"
    result = matching_service.match_against_job(job, candidate_text, candidate.skills)
    feedback = build_feedback(result.missing_skills)
    return CandidateMatchResponse(
        job_title=job.title,
        match_percentage=round(result.match_percentage, 2),
        similarity=round(result.similarity, 4),
        skill_score=round(result.skill_score, 4),
        title_score=round(result.title_score, 4),
        missing_skills=result.missing_skills,
        feedback=feedback,
        score_breakdown=result.score_breakdown,
        logs=result.logs,
    )


def rank_jobs_for_candidate(candidate: CandidateProfile, jobs: list[JobInput] | None = None) -> TopMatchesResponse:
    candidate_text = f"{candidate.headline}. {candidate.summary}. {' '.join(candidate.skills)}"
    target_jobs = jobs or [JobInput(**item) for item in SAMPLE_JOBS]
    matches: list[CandidateMatchResponse] = []

    for job in target_jobs:
        result = matching_service.match_against_job(job, candidate_text, candidate.skills)
        matches.append(
            CandidateMatchResponse(
                job_title=job.title,
                match_percentage=round(result.match_percentage, 2),
                similarity=round(result.similarity, 4),
                skill_score=round(result.skill_score, 4),
                title_score=round(result.title_score, 4),
                missing_skills=result.missing_skills,
                feedback=build_feedback(result.missing_skills),
                score_breakdown=result.score_breakdown,
                logs=result.logs,
            )
        )

    matches.sort(key=lambda item: item.match_percentage, reverse=True)
    for index, item in enumerate(matches, start=1):
        item.ranking = index

    return TopMatchesResponse(candidate_name=candidate.name, total_jobs=len(matches), matches=matches)


def rank_jobs_for_resume(file_bytes: bytes, filename: str, jobs: list[JobInput] | None = None) -> TopMatchesResponse:
    text = extract_text_from_resume(file_bytes, filename)
    if not text.strip():
        raise ValueError("Uploaded file is empty or unreadable.")

    if not jobs:
        recommendation = recommend_job_titles_from_cv_text(text, top_k=5)
        return TopMatchesResponse(
            candidate_name="Candidate from uploaded CV",
            total_jobs=recommendation.total_catalog,
            matches=recommendation.matches,
        )

    skill_extractor = SkillExtractor()
    extracted_skills = skill_extractor.extract(text)
    pseudo_candidate = CandidateProfile(
        name="Candidate from uploaded CV",
        headline="Uploaded CV",
        skills=extracted_skills,
        summary=text,
    )
    return rank_jobs_for_candidate(pseudo_candidate, jobs)


def compare_candidates_for_job(job: JobInput, candidates: list[CandidateProfile]) -> CandidateComparisonResponse:
    ranking: list[CandidateMatchResponse] = []

    for candidate in candidates:
        match = match_candidate_to_job(job, candidate)
        ranking.append(match)

    ranking.sort(key=lambda item: item.match_percentage, reverse=True)
    for index, item in enumerate(ranking, start=1):
        item.ranking = index

    return CandidateComparisonResponse(job_title=job.title, ranking=ranking)
