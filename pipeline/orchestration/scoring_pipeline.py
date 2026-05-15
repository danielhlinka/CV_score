from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol

from pipeline.lib.contracts import EnrichedCV, JobProfile, MatchResult, ParsedCV


class JobParserStep(Protocol):
    """Callable contract for parsing job-form payloads.
    Decouples orchestration from concrete parser implementation."""
    def __call__(self, form: Mapping[str, str]) -> JobProfile:
        """Parse web form fields into canonical job profile payload.
        Implementations should raise on invalid user input."""
        ...


class TextExtractorStep(Protocol):
    """Callable contract for reading CV text from staged files.
    Allows swapping extraction backends without orchestration changes."""
    def __call__(self, file_path: str) -> str:
        """Read raw text content from staged CV file path.
        Implementations should raise when file extraction fails."""
        ...


class CVParserStep(Protocol):
    """Callable contract for transforming raw CV text to parsed structure.
    Keeps normalization logic isolated behind a narrow interface."""
    def __call__(self, raw_text: str) -> ParsedCV:
        """Normalize raw CV text into structured parsed representation.
        Output must satisfy the `ParsedCV` contract."""
        ...


class CVEnricherStep(Protocol):
    """Callable contract for semantic/profile enrichment of parsed CV data.
    Supports dependency injection for tests and future model changes."""
    def __call__(self, parsed: ParsedCV) -> EnrichedCV:
        """Augment parsed CV data with semantic/enriched features.
        Output must satisfy the `EnrichedCV` contract."""
        ...


class MatcherStep(Protocol):
    """Callable contract for scoring an enriched CV against job profile.
    Returns the canonical match-result payload used by web/UI layers."""
    def __call__(self, cv: EnrichedCV, job: JobProfile) -> MatchResult:
        """Score enriched CV against target job requirements.
        Output must satisfy the `MatchResult` contract."""
        ...


class SanityCheckStep(Protocol):
    """Callable contract for non-blocking scoring diagnostics.
    Used to log suspicious outputs without mutating score results."""
    def __call__(self, result: MatchResult) -> None:
        """Run diagnostics/logging checks on computed score payload.
        Must not alter the supplied result object."""
        ...


class ExplainerStep(Protocol):
    """Callable contract for producing human-readable score explanations.
    Keeps LLM integration optional and pluggable."""
    def __call__(self, result: MatchResult) -> str:
        """Produce human-readable explanation for scoring result.
        Should return a safe fallback message on generation failure."""
        ...


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
        """Execute the full scoring workflow from form input to explanation.
        Coordinates parse, enrich, match, sanity logging, and explanation."""
        job_profile = self.parse_job(form)
        raw_text = self.extract_text(cv_path)
        parsed_cv = self.parse_cv(raw_text)
        enriched_cv = self.enrich_cv(parsed_cv)

        result = self.match(enriched_cv, job_profile)
        self.sanity_check(result)
        result["explanation"] = self.explain(result)
        return result


def build_scoring_orchestration_service() -> ScoringOrchestrationService:
    """Wire concrete pipeline steps into a ready-to-use orchestrator.
    Centralizes composition to keep route handlers thin."""
    from pipeline.enrich.profile_enricher import enrich_cv
    from pipeline.input.cv_text_extractor import extract_text
    from pipeline.input.job_profile_parser import parse_job
    from pipeline.output.explanation_service import explain
    from pipeline.output.sanity_logger import sanity_check
    from pipeline.lib.parser import parse_cv
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
