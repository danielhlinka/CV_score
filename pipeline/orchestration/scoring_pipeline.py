from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol

from pipeline.contracts import EnrichedCV, JobProfile, MatchResult, ParsedCV


class JobParserStep(Protocol):
    def __call__(self, form: Mapping[str, str]) -> JobProfile: ...


class TextExtractorStep(Protocol):
    def __call__(self, file_path: str) -> str: ...


class CVParserStep(Protocol):
    def __call__(self, raw_text: str) -> ParsedCV: ...


class CVEnricherStep(Protocol):
    def __call__(self, parsed: ParsedCV) -> EnrichedCV: ...


class MatcherStep(Protocol):
    def __call__(self, cv: EnrichedCV, job: JobProfile) -> MatchResult: ...


class SanityCheckStep(Protocol):
    def __call__(self, result: MatchResult) -> None: ...


class ExplainerStep(Protocol):
    def __call__(self, result: MatchResult) -> str: ...


@dataclass(slots=True)
class ScoringOrchestrationService:
    parse_job: JobParserStep
    extract_text: TextExtractorStep
    parse_cv: CVParserStep
    enrich_cv: CVEnricherStep
    match: MatcherStep
    sanity_check: SanityCheckStep
    explain: ExplainerStep

    def score(self, *, form: Mapping[str, str], cv_path: str) -> MatchResult:
        job_profile = self.parse_job(form)
        raw_text = self.extract_text(cv_path)
        parsed_cv = self.parse_cv(raw_text)
        enriched_cv = self.enrich_cv(parsed_cv)

        result = self.match(enriched_cv, job_profile)
        self.sanity_check(result)
        result["explanation"] = self.explain(result)
        return result


def build_scoring_orchestration_service() -> ScoringOrchestrationService:
    from pipeline.enrich.profile_enricher import enrich_cv
    from pipeline.input.cv_text_extractor import extract_text
    from pipeline.input.job_profile_parser import parse_job
    from pipeline.output.explanation_service import explain
    from pipeline.output.sanity_logger import sanity_check
    from pipeline.parser import parse_cv
    from pipeline.score.match_scorer import match

    return ScoringOrchestrationService(
        parse_job=parse_job,
        extract_text=extract_text,
        parse_cv=parse_cv,
        enrich_cv=enrich_cv,
        match=match,
        sanity_check=sanity_check,
        explain=explain,
    )
