from pipeline.output.explanation_service import (
    DEFAULT_EXPLAINER as _DEFAULT_EXPLAINER,
    DEFAULT_OPENAI_MODEL,
    GENERIC_FAILURE_MESSAGE,
    MISSING_API_KEY_MESSAGE,
    OpenAIExplainer,
)

DEFAULT_EXPLAINER = _DEFAULT_EXPLAINER


def explain(result: dict) -> str:
    """Backward-compatible proxy to the configured explainer instance.
    Keeps legacy imports working after module reorganization."""
    return DEFAULT_EXPLAINER.explain(result)


__all__ = [
    "DEFAULT_EXPLAINER",
    "DEFAULT_OPENAI_MODEL",
    "GENERIC_FAILURE_MESSAGE",
    "MISSING_API_KEY_MESSAGE",
    "OpenAIExplainer",
    "explain",
]
