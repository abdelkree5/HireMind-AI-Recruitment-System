from __future__ import annotations

from backend.app.services.skill_extractor import DEFAULT_SKILL_VOCAB, SkillExtractor as BackendSkillExtractor


class SkillExtractor(BackendSkillExtractor):
    def __init__(self, vocabulary: list[str] | None = None) -> None:
        super().__init__(vocabulary=vocabulary or DEFAULT_SKILL_VOCAB)
