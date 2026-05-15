# CV Scorer Architecture Documentation

This document explains the solution from an architectural perspective and then walks through every production module, class, and function. Its goal is fast onboarding: a reader should be able to understand the request flow, the data contracts, the module boundaries, and the reason each function exists.

## System Purpose

The application scores a candidate CV against a job profile submitted through a Flask web form. It accepts a PDF or DOCX CV, extracts text, normalizes the text into structured candidate signals, enriches those signals with semantic role and seniority inference, computes weighted match scores, logs sanity diagnostics, and optionally generates a Markdown explanation through OpenAI.

The solution is intentionally small and layered. The web layer handles HTTP, upload lifecycle, and templates. The pipeline layer handles domain processing. The orchestration layer wires pipeline steps together through callable interfaces. The compatibility layer preserves older import paths while the codebase has been reorganized into clearer subpackages.

## Runtime Request Flow

```text
GET /
  -> web.routes.index
  -> templates/index.html

POST /score
  -> web.routes.score
  -> UploadLifecycle.stage
  -> ScoringOrchestrationService.score
       -> parse_job
       -> extract_text
       -> parse_cv
       -> enrich_cv
       -> match
       -> sanity_check
       -> explain
  -> templates/results.html
  -> staged upload is removed by context manager cleanup
```

The main production path is composed in `pipeline/orchestration/scoring_pipeline.py`. The route does not know how CV parsing or scoring works; it only validates/stages the upload and calls the service.

## Architectural Layers

| Layer | Main files | Responsibility |
|---|---|---|
| Application bootstrap | `app.py`, `main.py` | Create and run the Flask app, configure logging, register routes and errors. |
| Web interface | `web/routes.py`, `web/uploads.py`, `web/errors.py`, `web/config.py` | Handle requests, upload validation, temporary file lifecycle, runtime settings, and error responses. |
| Input parsing | `pipeline/input/*` | Extract raw CV text from files and parse job form fields into a canonical job profile. |
| CV normalization | `pipeline/normalize/*` | Convert raw CV text into structured contact, skills, education, experience, role signals, seniority signals, confidence, and warnings. |
| Enrichment | `pipeline/enrich/*` | Build semantic embeddings, compare CV profiles against role/seniority templates, and derive enriched role/seniority metadata. |
| Scoring | `pipeline/score/*` | Score skills, seniority, experience, role, and education, then combine them with fixed weights. |
| Output | `pipeline/output/*` | Produce LLM explanation text and log sanity diagnostics. |
| Orchestration | `pipeline/orchestration/scoring_pipeline.py` | Compose concrete pipeline functions into one request-level scoring workflow. |
| Shared contracts | `pipeline/lib/contracts.py`, `pipeline/lib/constants.py` | Define typed payload shapes, taxonomies, ranks, weights, and keyword/template constants. |
| Compatibility imports | `pipeline/lib/*`, package `__init__.py` files, `web/scoring_service.py` | Preserve historical import paths while delegating to the newer structured modules. |
| UI templates | `templates/index.html`, `templates/results.html` | Render the browser form and final scoring results. |
| Tests | `tests/*` | Protect request behavior, upload cleanup, parser guardrails, scoring semantics, orchestration order, and explainer fallbacks. |

## Data Flow and Trust Boundaries

The uploaded CV is stored only as a temporary staged file while a request is being processed. `UploadLifecycle.stage` saves the file, yields its path to the scoring route, and deletes the staged file in a `finally` block.

Raw CV text is extracted locally from PDF or DOCX. The normalized and enriched CV payload does include `raw_text` in memory because `EnrichedCV` extends `ParsedCV`, but the OpenAI explainer prompt is built only from selected structured fields such as seniority, years, skills, education, role category, job requirements, and score breakdown. The full raw CV text is not interpolated into `_build_prompt`.

The embedding layer first attempts to use the local `all-MiniLM-L6-v2` sentence-transformers model. If local loading fails, it attempts normal model loading. If that also fails, it falls back to deterministic hash embeddings so the application can still compute stable semantic-like scores.

The application has no database. Persistent state is limited to logs such as `app.log`; uploaded files are transient.

## Core Contracts

The codebase uses `TypedDict` contracts rather than Pydantic or dataclass domain models. These types provide static structure but do not enforce runtime validation by themselves.

| Contract | Defined in | Meaning |
|---|---|---|
| `ContactInfo` | `pipeline/lib/contracts.py` | Candidate email and phone, each nullable. |
| `ExperienceEntry` | `pipeline/lib/contracts.py` | One parsed work interval with title, start year, end year, duration, and original range text. |
| `NormalizedCV` | `pipeline/lib/contracts.py` | Structured parser output from raw text: contact, experience, skills, education, keyword signals, confidence, and warnings. |
| `ParsedCV` | `pipeline/lib/contracts.py` | Raw text plus normalized output and backward-compatible top-level contact fields. |
| `EnrichedCV` | `pipeline/lib/contracts.py` | Parsed CV plus semantic role/seniority scores, inferred categories, jobs, total experience score, skills, education, and parser metadata. |
| `JobProfile` | `pipeline/lib/contracts.py` | Canonical job requirements parsed from the form. |
| `ScoreBreakdown` | `pipeline/lib/contracts.py` | Per-component scoring values in the `0.0` to `1.0` range. |
| `MatchResult` | `pipeline/lib/contracts.py` | Final result containing score, breakdown, parser metadata, enriched CV, job profile, and optional explanation. |

## Scoring Model

All component scores are floats between `0.0` and `1.0`. The final score is the weighted sum, rounded to three decimals.

| Component | Weight | Main rule |
|---|---:|---|
| Skills | 0.40 | Exact required-skill hits blended with semantic similarity for unmatched skills. |
| Seniority | 0.25 | Rank distance between inferred CV seniority and requested job seniority, softened when parser confidence is lower. |
| Experience | 0.25 | Candidate years divided by required years, capped at `1.0`, with conservative fallback scores when experience extraction is uncertain. |
| Role | 0.05 | Category match between inferred CV role and requested job role, with weaker penalties under low confidence. |
| Education | 0.05 | Rank comparison between candidate education and required education. |

## Active Pipeline Versus Compatibility Layer

The active architecture lives mostly under `pipeline/input`, `pipeline/normalize`, `pipeline/enrich`, `pipeline/score`, `pipeline/output`, and `pipeline/orchestration`.

The `pipeline/lib` package is partly a shared library and partly a compatibility layer. `pipeline/lib/constants.py` and `pipeline/lib/contracts.py` are core shared modules. Other files such as `pipeline/lib/extractor.py`, `pipeline/lib/normalizer.py`, `pipeline/lib/semantic.py`, `pipeline/lib/experience.py`, and `pipeline/lib/job_parser.py` re-export functions from the newer packages. `pipeline/lib/embedder.py` and `pipeline/lib/matcher.py` preserve older full implementations that mirror the new enrichment and scoring behavior for legacy imports and tests.

This means similar names appear twice. For example, the current scoring implementation is in `pipeline/score/score_components.py` and `pipeline/score/match_scorer.py`, while `pipeline/lib/matcher.py` keeps older `_skills_score`, `_experience_score`, and `match` functions alive.

## Module and Function Reference

### `app.py`

`app.py` is the Flask application factory and default executable entry point.

| Function or object | Purpose |
|---|---|
| `create_app(test_config=None)` | Builds the Flask app, loads runtime config, applies optional test overrides, ensures the upload folder exists, registers the web blueprint, and registers centralized error handlers. |
| `app` | Module-level Flask app created by `create_app()` for direct `python app.py` execution and WSGI-style imports. |
| `if __name__ == "__main__"` block | Runs the app with debug/reloader controlled by `RUN_DEBUG`. |

### `main.py`

`main.py` is a tiny compatibility runner.

| Function or object | Purpose |
|---|---|
| `app` import | Imports the module-level Flask app from `app.py`. |
| `if __name__ == "__main__"` block | Runs the imported app with the same debug/reloader behavior as `app.py`. |

### `web/config.py`

This module centralizes environment-driven runtime configuration.

| Function or object | Purpose |
|---|---|
| `DEFAULT_MAX_UPLOAD_MB` | Default upload limit, currently `10` MB. |
| `TRUTHY_ENV_VALUES` | Accepted truthy strings for debug mode parsing. |
| `read_max_upload_bytes()` | Reads `MAX_UPLOAD_MB`, validates that it is a positive integer, logs warnings for invalid values, and returns bytes for Flask `MAX_CONTENT_LENGTH`. |
| `read_debug_mode()` | Reads `FLASK_DEBUG` and returns `True` only for explicit truthy values. |
| `resolve_upload_folder(base_dir)` | Reads `UPLOAD_FOLDER`, resolves relative paths against the application base directory, creates the directory, and returns a `Path`. |
| `runtime_config(base_dir)` | Assembles the Flask config dictionary: base dir, upload folder, max content length, and debug flag. |

### `web/uploads.py`

This module owns upload safety and lifecycle. It keeps file validation and cleanup outside the route handler.

| Function, class, or method | Purpose |
|---|---|
| `ValidatedUpload` | Frozen dataclass containing the original `FileStorage` and sanitized filename after validation. |
| `StagedUpload` | Frozen dataclass containing the safe original name and generated temporary path. |
| `UploadLifecycle.__init__(upload_folder, allowed_extensions)` | Normalizes allowed extensions, rejects empty extension policies, stores the upload folder, and ensures the directory exists. |
| `UploadLifecycle.allowed_extensions` | Read-only property exposing the immutable extension allow-list. |
| `UploadLifecycle.validate(file_storage)` | Checks that the upload exists, has a filename, sanitizes the filename, verifies the extension, and returns `ValidatedUpload`; raises HTTP errors for invalid input. |
| `UploadLifecycle.build_unique_path(safe_name)` | Builds a collision-resistant staged filename by preserving the stem and normalized suffix while adding an 8-character UUID segment. |
| `UploadLifecycle._cleanup(staged_path)` | Best-effort deletion of a staged file; logs cleanup failures without raising. |
| `UploadLifecycle.stage(file_storage)` | Context manager that validates, saves, yields `StagedUpload`, and guarantees cleanup on success or failure. Save failures are wrapped as `InternalServerError`. |

### `web/errors.py`

This module provides consistent HTML or JSON error behavior for the Flask app.

| Function | Purpose |
|---|---|
| `is_html_request()` | Compares request `Accept` preferences to decide whether to render HTML or return JSON. |
| `error_response(message, status_code)` | Renders `index.html` with `error_message` for browser requests or returns `{"error": message}` for API-style requests. |
| `register_error_handlers(app)` | Registers all error handlers on the Flask app. |
| `handle_request_too_large(exc)` | Nested handler for `RequestEntityTooLarge`; returns status `413` with the configured MB limit. |
| `handle_bad_request(exc)` | Nested handler for `BadRequest`; returns status `400`. |
| `handle_unsupported_media_type(exc)` | Nested handler for `UnsupportedMediaType`; returns status `415`. |
| `handle_unprocessable_entity(exc)` | Nested handler for `UnprocessableEntity`; returns status `422`. |
| `handle_http_exception(exc)` | Nested catch-all handler for other Werkzeug HTTP exceptions. |
| `handle_unexpected_error(exc)` | Nested final handler for unexpected exceptions; logs and returns status `500`. |

### `web/routes.py`

This module is the HTTP interface. It keeps route handlers thin and delegates work to upload and scoring services.

| Function or object | Purpose |
|---|---|
| `web_bp` | Flask blueprint containing the browser routes. |
| `get_scoring_service()` | Cached factory for the scoring orchestration service. `lru_cache(maxsize=1)` avoids rebuilding dependencies on every request. |
| `_build_uploader()` | Creates an `UploadLifecycle` using the current app upload folder and supported CV extensions. |
| `index()` | Handles `GET /` and renders the submission form. |
| `score()` | Handles `POST /score`: stages the uploaded CV, calls `service.score`, maps domain/IO errors to HTTP exceptions, and renders `results.html`. |

### `web/scoring_service.py`

This module is a compatibility export surface for orchestration.

| Export | Purpose |
|---|---|
| `ExplainerStep`, `MatcherStep`, `SanityCheckStep`, `ScoringOrchestrationService`, `build_scoring_orchestration_service` | Re-exported from `pipeline/orchestration/scoring_pipeline.py` so web code and tests can keep importing from `web.scoring_service`. |

### `web/__init__.py`

This package initializer re-exports the web blueprint and error registration function.

| Export | Purpose |
|---|---|
| `register_error_handlers` | Public package-level access to central error registration. |
| `web_bp` | Public package-level access to the Flask blueprint. |

### `pipeline/lib/constants.py`

This module defines domain vocabularies, ranks, keyword maps, and semantic templates.

| Constant or type | Purpose |
|---|---|
| `RoleCategory` | Literal type for all internally detectable role categories, including categories that are not exposed in the job form. |
| `JobRoleCategory` | Literal type for user-selectable job role categories. |
| `SeniorityLevel` | Literal type for supported seniority levels. |
| `EducationLevel` | Literal type for supported education levels. |
| `ConfidenceLevel` | Literal type for parser confidence values. |
| `ROLE_CATEGORIES`, `JOB_ROLE_CATEGORIES`, `SENIORITY_ORDER`, `EDUCATION_ORDER` | Ordered canonical category lists. |
| `VALID_ROLE_CATEGORIES`, `VALID_SENIORITY`, `VALID_EDUCATION` | Frozen validation sets used by job parsing. |
| `SENIORITY_LEVEL_RANK`, `EDUCATION_LEVEL_RANK` | Rank maps used for distance-based scoring. |
| `ROLE_TEMPLATES` | Text templates embedded for semantic role classification. |
| `SENIORITY_TEMPLATES` | Text templates embedded for semantic seniority classification. |
| `ROLE_SIGNAL_KEYWORDS` | Keyword groups counted during normalization to produce deterministic role signals. |
| `SENIORITY_SIGNAL_KEYWORDS` | Keyword groups counted during normalization to produce deterministic seniority signals. |

### `pipeline/lib/contracts.py`

This module declares the payload shapes shared across the pipeline.

| Class | Purpose |
|---|---|
| `ContactInfo` | Typed dictionary for nullable email and phone. |
| `ExperienceEntry` | Typed dictionary for a normalized work experience interval. |
| `NormalizedCV` | Typed dictionary for normalized parser output. |
| `ParsedCV` | Typed dictionary for raw and normalized CV data. |
| `EnrichedCV` | Typed dictionary for parsed CV data plus semantic and scoring helper fields. |
| `JobProfile` | Typed dictionary for validated job requirements. |
| `ScoreBreakdown` | Typed dictionary for component scores. |
| `MatchResult` | Typed dictionary for final output returned by the matcher and completed by the explainer. |

### `pipeline/input/cv_text_extractor.py`

This module extracts plain text from supported CV files.

| Function or object | Purpose |
|---|---|
| `SUPPORTED_EXTENSIONS` | Allowed CV file suffixes: `.pdf` and `.docx`. |
| `extract_text(file_path)` | Dispatches by file extension, rejects unsupported types, and returns extracted text. |
| `_extract_from_pdf(file_path)` | Uses `pdfplumber` to concatenate text from PDF pages and raises when no text can be extracted. |
| `_extract_from_docx(file_path)` | Uses `python-docx` to concatenate non-empty paragraphs and table-cell rows. |

### `pipeline/input/job_profile_parser.py`

This module converts raw web form values into a validated `JobProfile`.

| Function | Purpose |
|---|---|
| `_normalized_choice(value, field_name, allowed_values, default)` | Normalizes enum-like fields, applies a default for blank input, and raises `BadRequest` for invalid values. |
| `_parse_years_required(form)` | Parses years required, defaults blank input to `0`, rejects non-integers, negative values, and values over `50`. |
| `parse_job(form)` | Requires `job_title`, deduplicates comma-separated skills in first-seen order, validates seniority/education/role category, and returns `JobProfile`. |

### `pipeline/normalize/contact_parser.py`

This module extracts basic contact details from raw CV text.

| Function | Purpose |
|---|---|
| `extract_email(text)` | Finds the first email-like token or returns `None`. |
| `extract_phone(text)` | Finds the first phone-number-like token with common separators or returns `None`. |

### `pipeline/normalize/education_parser.py`

This module maps education keywords to the highest detected education level.

| Function | Purpose |
|---|---|
| `extract_education(text)` | Checks text for PhD, master, bachelor, and high-school keywords in descending order and returns a normalized level or `none`. |

### `pipeline/normalize/skills_parser.py`

This module extracts canonical skill labels from CV text.

| Function or object | Purpose |
|---|---|
| `SKILL_GROUPS` | Maps canonical grouped skills to variants; for example Spark variants collapse to `spark`. |
| `KNOWN_SKILLS` | Flat list of individual skills and work practices to detect. |
| `extract_skills(text)` | Searches grouped variants first, then known skills, deduplicating while preserving readable first-seen ordering. |

### `pipeline/normalize/experience_parser.py`

This module is the most heuristic parser in the system. It extracts work date ranges, filters likely education ranges, merges overlapping intervals, and calculates total experience.

| Function, class, or method | Purpose |
|---|---|
| `PRESENT_TOKENS` | Localized tokens that mean the end date is the current month. |
| `DATE_RANGE_PATTERN` | Regex for `YYYY - YYYY`, `MM/YYYY - MM/YYYY`, and present/current end tokens. |
| `NOISE_LINE_PATTERNS` | Regexes for lines that should not be treated as useful title/context lines. |
| `EDUCATION_CONTEXT_PATTERN` | Regex indicating a date range may refer to education. |
| `WORK_CONTEXT_PATTERN` | Regex indicating a date range may refer to work experience. |
| `_ParsedDateToken` | Internal frozen dataclass storing parsed year and month. |
| `_ParsedDateToken.month_index` | Converts the parsed date to a monotonic month coordinate. |
| `_ExperienceCandidate` | Internal frozen dataclass for an extracted candidate interval before output cleanup. |
| `_ExperienceCandidate.dedupe_key` | Stable key used to collapse duplicate candidates by title and month boundaries. |
| `_ExperienceCandidate.as_entry()` | Converts the internal candidate to the public `ExperienceEntry` shape. |
| `_is_noise_line(text)` | Rejects empty, punctuation-only, too-short, URL/contact, or known navigation lines. |
| `_parse_date_token(token, is_start, now)` | Parses present/current tokens, `MM/YYYY`, or bare years into `(year, month)`. Bare start years use January; bare end years use December. |
| `_to_month_index(year, month)` | Converts a date into `year * 12 + month_offset` for interval math. |
| `_resolve_line_context(lines, index)` | Returns previous and next non-empty lines around a candidate line. |
| `_has_work_and_education_context(context_text, prefix_text)` | Determines whether a date range looks educational, work-related, or both. Short useful prefixes count as work context. |
| `_resolve_title(prefix_text, prev_line)` | Chooses the best title from text before the date range or the previous line, falling back to `unknown`. |
| `_parse_date_tokens(start_token, end_token, now)` | Parses and validates date range ordering, returning internal date tokens or `None`. |
| `_build_candidate_from_match(line, prev_line, next_line, match, now)` | Converts a regex match into an `_ExperienceCandidate`, also reporting whether it was skipped as education. |
| `_deduplicate_candidates(candidates)` | Deduplicates candidates by key and sorts them by start month. |
| `_merge_intervals(intervals)` | Merges overlapping or adjacent month intervals to avoid double-counting experience. |
| `_determine_experience_confidence(entries, total_years)` | Returns `high`, `medium`, or `low` based on entry count, recognized titles, and total duration. |
| `_build_experience_warnings(skipped_education_ranges, confidence)` | Creates warnings for skipped education ranges and non-high confidence. |
| `_clean_experience_entries(entries)` | Converts candidates to public entries and sorts newest first. |
| `parse_experience_entries(text)` | Main public function: scans lines for date ranges, builds candidates, filters education-only ranges, deduplicates, merges intervals, calculates total years, confidence, warnings, and clean entries. |

### `pipeline/normalize/cv_normalizer.py`

This module coordinates the lower-level parsers into one normalized CV object.

| Function | Purpose |
|---|---|
| `_keyword_signals(text, mapping)` | Counts whole-word keyword hits per role or seniority bucket. |
| `_determine_parser_confidence(experience_confidence, skills_count, has_experience_entries)` | Starts from experience confidence and downgrades when skills or entries are sparse. |
| `_build_normalizer_warnings(experience_warnings, skills, education)` | Combines experience warnings with missing-skill and missing-education warnings. |
| `normalize_cv_text(raw_text)` | Extracts contact, experience, skills, education, role signals, seniority signals, strongest signals, parser confidence, and warnings into `NormalizedCV`. |

### `pipeline/lib/parser.py`

This module wraps normalization into the downstream `ParsedCV` contract.

| Function | Purpose |
|---|---|
| `parse_cv(raw_text)` | Calls `normalize_cv_text`, copies top-level email/phone for compatibility, stores raw text and length, and returns `ParsedCV`. |

### `pipeline/enrich/embedding_provider.py`

This module owns embedding generation and the low-level role-label classifier.

| Function or object | Purpose |
|---|---|
| `_CATEGORY_EMBEDDINGS` | In-memory cache for role category label embeddings used by `classify_role`. |
| `_get_model()` | Cached loader for `SentenceTransformer("all-MiniLM-L6-v2")`; tries local files first, then normal load, then returns `False` sentinel on failure. |
| `_hash_embedding(text, dims=384)` | Deterministic token-hash vector fallback, normalized to unit length when possible. |
| `embed_text(text)` | Returns a transformer embedding, fallback hash embedding, or zero vector for blank text. |
| `get_embedding(text)` | Public alias retained for import stability. |
| `classify_role(title)` | Embeds a title and each role category label, computes cosine similarity, caches category embeddings, and returns the best `RoleCategory`. |

### `pipeline/enrich/semantic_similarity.py`

This module provides reusable embedding similarity utilities.

| Function or type | Purpose |
|---|---|
| `Embedding` | Type alias for NumPy floating arrays. |
| `cosine_score(left, right)` | Computes cosine similarity and returns a Python float. |
| `template_scores(profile, templates)` | Scores one profile embedding against labeled template embeddings. |
| `best_cosine_score(target, candidates, default=0.0)` | Returns the highest similarity across candidate embeddings or the default for empty input. |
| `memoized_embedding(text)` | LRU-cached wrapper around `get_embedding` to avoid repeated embedding work. |

### `pipeline/enrich/seniority_model.py`

This module turns years of experience into smooth seniority priors and combines those priors with semantic scores.

| Function or object | Purpose |
|---|---|
| `experience_score(years, k=3.0)` | Converts years of experience into a monotonic saturating score in `[0, 1]`. |
| `_bell(years, peak, width)` | Computes bell-curve affinity around a seniority-specific peak. |
| `LEVEL_CURVES` | Maps seniority levels to experience-year affinity curves. |
| `combined_seniority(sen_scores, years)` | Multiplies semantic seniority scores by experience priors and returns the best level plus full combined map. |

### `pipeline/enrich/profile_enricher.py`

This module enriches `ParsedCV` into `EnrichedCV`.

| Function | Purpose |
|---|---|
| `_get_role_template_embeddings()` | Cached embedding map for role templates. |
| `_get_seniority_template_embeddings()` | Cached embedding map for seniority templates. |
| `_normalized_signal_scores(signals)` | Converts integer keyword counts into normalized `0.0` to `1.0` scores. |
| `enrich_cv(parsed)` | Builds compact semantic profiles from skills, job titles, role hints, seniority hints, and years; scores role and seniority templates; blends semantic and keyword signals; chooses top two roles; computes total experience score; carries parser metadata forward. |

### `pipeline/score/score_weights.py`

This module defines final score weights.

| Object | Purpose |
|---|---|
| `WEIGHTS` | Component weights: skills `0.40`, seniority `0.25`, experience `0.25`, role `0.05`, education `0.05`. |

### `pipeline/score/score_components.py`

This module contains each independently testable scoring component.

| Function | Purpose |
|---|---|
| `skills_score(cv, job)` | Returns `1.0` when no job skills are required; otherwise computes exact required-skill coverage and blends semantic similarity for unmatched requirements. Empty extracted skills receive a low-confidence fallback of `0.5`, otherwise `0.0`. |
| `seniority_score(cv, job)` | Compares seniority ranks and applies confidence-dependent penalties. Low confidence never drops below `0.5`; medium confidence never drops below `0.35`. |
| `experience_score_component(cv, job)` | Returns `1.0` when no years are required; otherwise divides candidate years by required years and caps at `1.0`. Missing years receive confidence-dependent fallback scores. |
| `role_score(cv, job)` | Scores role-category match. Missing roles return `0.5`; low-confidence mismatches return `0.5`; low-confidence matches return `0.8`; high/medium matches return `1.0`; high/medium mismatches return `0.2`. |
| `education_score(cv, job)` | Compares education ranks and penalizes only when the candidate level is below the requirement. |

### `pipeline/score/match_scorer.py`

This module aggregates component scores into a final result.

| Function | Purpose |
|---|---|
| `match(cv, job)` | Calls every component scorer, multiplies by `WEIGHTS`, rounds the final score, and returns `MatchResult` with parser confidence, warnings, enriched CV, and job profile. |

### `pipeline/output/sanity_logger.py`

This module adds observability around extracted fields and scores.

| Function | Purpose |
|---|---|
| `sanity_check(result)` | Logs extracted seniority, experience, education, role, skill count, parser confidence, parser warnings, score components, and final score. It emits warnings for no skills, implausible experience over 50 years, out-of-range final score, unknown seniority, missing education, and low parser confidence. |

### `pipeline/output/explanation_service.py`

This module integrates with OpenAI while keeping the explainer injectable and failure-tolerant.

| Function, class, or object | Purpose |
|---|---|
| `DEFAULT_OPENAI_MODEL` | Reads `OPENAI_MODEL` from the environment or defaults to `gpt-4o-mini`. |
| `MISSING_API_KEY_MESSAGE` | Stable fallback message when `OPENAI_API_KEY` is absent. |
| `GENERIC_FAILURE_MESSAGE` | Stable fallback message for API/runtime failures or empty responses. |
| `ClientFactory` | Callable type for constructing a client, used to inject fakes in tests. |
| `_build_openai_client(api_key)` | Creates an `OpenAI` client for the given key. |
| `_build_prompt(result)` | Builds the Markdown-report prompt from selected structured CV/job/score fields. It expects required result keys and raises `KeyError` if the result shape is missing them. |
| `_extract_response_content(response)` | Safely reads the first chat-completion message content or returns an empty string. |
| `OpenAIExplainer` | Frozen dataclass configuring model, API-key env var, max tokens, and client factory. |
| `OpenAIExplainer.explain(result)` | Builds the prompt, checks for API key, calls the OpenAI chat completions API, logs failures, and returns generated content or a stable fallback message. |
| `DEFAULT_EXPLAINER` | Module-level explainer instance used by the public wrapper. |
| `explain(result)` | Compatibility wrapper that delegates to `DEFAULT_EXPLAINER.explain`. |

### `pipeline/orchestration/scoring_pipeline.py`

This module is the composition root for the domain pipeline.

| Function, class, or method | Purpose |
|---|---|
| `JobParserStep.__call__(form)` | Protocol contract for parsing request form data into `JobProfile`. |
| `TextExtractorStep.__call__(file_path)` | Protocol contract for extracting raw text from a staged CV file. |
| `CVParserStep.__call__(raw_text)` | Protocol contract for turning raw text into `ParsedCV`. |
| `CVEnricherStep.__call__(parsed)` | Protocol contract for turning parsed CV data into `EnrichedCV`. |
| `MatcherStep.__call__(cv, job)` | Protocol contract for returning `MatchResult`. |
| `SanityCheckStep.__call__(result)` | Protocol contract for non-mutating diagnostics. |
| `ExplainerStep.__call__(result)` | Protocol contract for producing human-readable explanation text. |
| `ScoringOrchestrationService` | Dataclass containing all pipeline step callables. |
| `ScoringOrchestrationService.score(form, cv_path)` | Runs steps in order: parse job, extract text, parse CV, enrich CV, match, sanity check, explain. It mutates the match result only by setting `result["explanation"]`. |
| `build_scoring_orchestration_service()` | Imports concrete functions lazily and returns a fully wired service instance. Lazy imports reduce import-time coupling and make the composition point explicit. |

### `pipeline/__init__.py`

This package initializer re-exports shared constants and contracts from `pipeline/lib`.

| Export group | Purpose |
|---|---|
| Constants and literal types | Provides package-level access to role, seniority, education, confidence, rank, keyword, and template definitions. |
| Contract types | Provides package-level access to all `TypedDict` payload contracts. |

### `pipeline/input/__init__.py`

This initializer exposes input-layer functions.

| Export | Purpose |
|---|---|
| `SUPPORTED_EXTENSIONS`, `extract_text`, `parse_job` | Public input-layer API for file extraction and job form parsing. |

### `pipeline/normalize/__init__.py`

This initializer exposes normalization functions.

| Export | Purpose |
|---|---|
| `extract_education`, `extract_skills`, `normalize_cv_text` | Public normalization API. |

### `pipeline/enrich/__init__.py`

This initializer exposes enrichment functions and semantic helpers.

| Export | Purpose |
|---|---|
| `classify_role`, `embed_text`, `get_embedding` | Embedding and role-classification helpers. |
| `enrich_cv` | Main enrichment entry point. |
| `combined_seniority`, `experience_score` | Seniority/experience scoring helpers. |
| `Embedding`, `best_cosine_score`, `cosine_score`, `memoized_embedding`, `template_scores` | Semantic similarity API. |

### `pipeline/score/__init__.py`

This initializer exposes scoring functions.

| Export | Purpose |
|---|---|
| `WEIGHTS`, `education_score`, `experience_score_component`, `match`, `role_score`, `seniority_score`, `skills_score` | Public scoring API. |

### `pipeline/output/__init__.py`

This initializer exposes output-layer functions.

| Export | Purpose |
|---|---|
| `OpenAIExplainer`, `explain`, `sanity_check` | Public explanation and diagnostics API. |

### `pipeline/orchestration/__init__.py`

This initializer exposes orchestration contracts and factory.

| Export | Purpose |
|---|---|
| `ExplainerStep`, `MatcherStep`, `SanityCheckStep`, `ScoringOrchestrationService`, `build_scoring_orchestration_service` | Public orchestration API. |

## Compatibility Modules in `pipeline/lib`

These modules exist so older imports continue to work. They are part of the solution because tests and current web code still depend on some of them.

### `pipeline/lib/__init__.py`

This package initializer only documents that `pipeline/lib` contains compatibility modules for pipeline internals.

### `pipeline/lib/extractor.py`

| Export | Purpose |
|---|---|
| `SUPPORTED_EXTENSIONS`, `extract_text` | Re-exported from `pipeline/input/cv_text_extractor.py`. |
| `extract_education` | Re-exported from `pipeline/normalize/education_parser.py`. |
| `extract_skills` | Re-exported from `pipeline/normalize/skills_parser.py`. |

### `pipeline/lib/normalizer.py`

| Export | Purpose |
|---|---|
| `normalize_cv_text` | Re-exported from `pipeline/normalize/cv_normalizer.py`. |

### `pipeline/lib/embeddings.py`

| Export | Purpose |
|---|---|
| `classify_role`, `embed_text`, `get_embedding` | Re-exported from `pipeline/enrich/embedding_provider.py`. |

### `pipeline/lib/semantic.py`

| Export | Purpose |
|---|---|
| `Embedding`, `best_cosine_score`, `cosine_score`, `memoized_embedding`, `template_scores` | Re-exported from `pipeline/enrich/semantic_similarity.py`. |

### `pipeline/lib/experience.py`

| Export | Purpose |
|---|---|
| `LEVEL_CURVES`, `combined_seniority`, `experience_score` | Re-exported from `pipeline/enrich/seniority_model.py`. |

### `pipeline/lib/job_parser.py`

| Export | Purpose |
|---|---|
| `parse_job` | Re-exported from `pipeline/input/job_profile_parser.py`. |

### `pipeline/lib/sanity_check.py`

| Export | Purpose |
|---|---|
| `sanity_check` | Re-exported from `pipeline/output/sanity_logger.py`. |

### `pipeline/lib/explainer.py`

| Function or export | Purpose |
|---|---|
| `DEFAULT_EXPLAINER` | Alias to `pipeline.output.explanation_service.DEFAULT_EXPLAINER`. |
| `DEFAULT_OPENAI_MODEL`, `GENERIC_FAILURE_MESSAGE`, `MISSING_API_KEY_MESSAGE`, `OpenAIExplainer` | Re-exported explainer configuration and type. |
| `explain(result)` | Backward-compatible proxy that delegates to `DEFAULT_EXPLAINER.explain`. |

### `pipeline/lib/embedder.py`

This is the legacy enrichment implementation. It mirrors `pipeline/enrich/profile_enricher.py` but imports through the compatibility surface.

| Function | Purpose |
|---|---|
| `_get_role_template_embeddings()` | Cached embedding map for role templates through legacy imports. |
| `_get_seniority_template_embeddings()` | Cached embedding map for seniority templates through legacy imports. |
| `_normalized_signal_scores(signals)` | Normalizes keyword counts for legacy enrichment. |
| `enrich_cv(parsed)` | Legacy enrichment entry point that creates role/seniority semantic scores, chooses role categories, calculates experience score, and carries parser metadata forward. |

### `pipeline/lib/matcher.py`

This is the legacy scoring implementation. It mirrors the modern scoring package while keeping older private function names used by tests.

| Function or object | Purpose |
|---|---|
| `WEIGHTS` | Legacy local copy of component weights. |
| `_skills_score(cv, job)` | Legacy skills score with exact and semantic matching. |
| `_seniority_score(cv, job)` | Legacy seniority rank-distance score with confidence guardrails. |
| `_experience_score(cv, job)` | Legacy experience sufficiency score with confidence fallbacks. |
| `_role_score(cv, job)` | Legacy role-category alignment score. |
| `_education_score(cv, job)` | Legacy education rank score. |
| `match(cv, job)` | Legacy weighted final score aggregator returning `MatchResult`. |

## Templates

### `templates/index.html`

This template renders the job-profile form and CV upload control. It posts to `/score` with `multipart/form-data`, includes fields matching `parse_job` expectations, restricts the file picker to `.pdf,.docx`, disables the submit button on submit, and shows a loading indicator.

### `templates/results.html`

This template renders the final score, component breakdown, candidate summary, parser quality, parser warnings, job requirements, and explanation. It uses `marked` to render Markdown from the explainer and `DOMPurify` to sanitize the resulting HTML before injecting it into the page.

## Test Suite Map

The tests are part of the learning path because they show which behaviors are treated as stable contracts.

| Test module or function | Protected behavior |
|---|---|
| `tests/test_core_behavior.py` | End-to-end web and parser basics. |
| `CoreBehaviorTests.test_parse_job_rejects_non_numeric_years_required` | Invalid years input produces a `BadRequest` with the expected message. |
| `CoreBehaviorTests.test_index_route_returns_ok` | `GET /` renders successfully. |
| `CoreBehaviorTests.test_score_missing_file_returns_bad_request_json` | Missing upload returns JSON `400` when JSON is requested. |
| `CoreBehaviorTests.test_score_unsupported_extension_returns_415_json` | Unsupported upload extension returns JSON `415` and mentions allowed extensions. |
| `CoreBehaviorTests.test_score_deletes_uploaded_temp_file_after_success` | Successful `/score` request removes the staged upload file. |
| `CoreBehaviorTests.test_extract_skills_canonicalizes_spark_and_keeps_snowflake` | Skill extraction canonicalizes Spark variants while preserving Snowflake. |
| `tests/test_uploads_behavior.py` | Upload validation, unique path generation, cleanup, and save-error wrapping. |
| `UploadLifecycleTests._make_uploader` | Test helper for creating upload lifecycle instances. |
| `UploadLifecycleTests.test_validate_keeps_existing_error_messages` | Upload validation errors remain stable. |
| `UploadLifecycleTests.test_build_unique_path_uses_folder_and_normalizes_suffix` | Staged filenames use the upload folder, UUID suffix, and lowercased extension. |
| `UploadLifecycleTests.test_stage_cleans_up_file_on_success_and_failure_paths` | Staged files are removed on both normal and exceptional context exits. |
| `UploadLifecycleTests.test_stage_wraps_save_oserror_with_compatible_http_error` | Save failures become `InternalServerError` and partial files are removed. |
| `tests/test_scoring_orchestration_service.py` | Orchestration ordering and result contract preservation. |
| `ScoringOrchestrationServiceTests.test_score_runs_pipeline_steps_in_expected_order` | The service calls parse/extract/parse/enrich/match/sanity/explain in the expected order. |
| `ScoringOrchestrationServiceTests.test_score_preserves_match_contract_and_overwrites_explanation` | The service preserves the match result object and replaces stale explanation text. |
| `tests/test_normalizer_behavior.py` | CV normalization guardrails. |
| `NormalizerBehaviorTests.test_education_ranges_are_excluded_from_experience` | Education date ranges are excluded from work experience. |
| `NormalizerBehaviorTests.test_parser_confidence_falls_back_when_skills_are_sparse` | Sparse skills can downgrade parser confidence even when experience confidence is high. |
| `NormalizerBehaviorTests.test_warnings_shape_for_sparse_text` | Sparse text produces stable warnings as strings. |
| `tests/test_semantic_scoring_behavior.py` | Semantic and confidence-aware scoring behavior. |
| `SemanticScoringBehaviorTests.test_parser_confidence_guardrails_for_skills_and_experience` | Low-confidence missing data receives conservative fallback scores. |
| `SemanticScoringBehaviorTests.test_skills_score_blends_exact_and_semantic_similarity` | Skills scoring blends exact match and semantic similarity. |
| `SemanticScoringBehaviorTests.test_embedder_template_cache_and_output_schema_stay_stable` | Legacy enrichment caches templates and preserves output schema. |
| `tests/test_explainer_behavior.py` | OpenAI explainer fallback and success paths. |
| `_sample_result` | Test helper returning a representative match result. |
| `_response_with_text` | Test helper mimicking an OpenAI response. |
| `_ClientWithCreate.__init__` | Test fake that exposes `chat.completions.create`. |
| `ExplainerBehaviorTests.test_missing_openai_api_key_returns_existing_message` | Missing API key returns the stable missing-key message. |
| `ExplainerBehaviorTests.test_api_error_returns_existing_generic_message` | API errors return the stable generic failure message. |
| `ExplainerBehaviorTests.test_empty_response_content_returns_existing_generic_message` | Empty responses return the stable generic failure message. |
| `ExplainerBehaviorTests.test_successful_response_returns_generated_content` | Successful API response returns generated Markdown and sends expected model/token/messages parameters. |
| `ExplainerBehaviorTests.test_public_explain_function_keeps_compatibility` | Legacy `pipeline.lib.explainer.explain` delegates to the default explainer. |
| `ExplainerBehaviorTests.test_missing_expected_result_keys_still_raises_key_error` | Missing required result keys still raise `KeyError`, documenting that `_build_prompt` expects the match contract. |

## Learning Path for a New Developer

Start with `app.py` to understand application creation. Then read `web/routes.py` and `web/uploads.py` to understand request handling and upload cleanup. Next read `pipeline/orchestration/scoring_pipeline.py`; it is the best high-level map of the full business workflow.

After that, follow the data contracts in `pipeline/lib/contracts.py` and constants in `pipeline/lib/constants.py`. Then read the pipeline in execution order: `pipeline/input/job_profile_parser.py`, `pipeline/input/cv_text_extractor.py`, `pipeline/lib/parser.py`, `pipeline/normalize/cv_normalizer.py`, `pipeline/enrich/profile_enricher.py`, `pipeline/score/match_scorer.py`, `pipeline/output/sanity_logger.py`, and `pipeline/output/explanation_service.py`.

Read `pipeline/lib/*` after the main flow. Treat most of it as compatibility infrastructure, except `constants.py`, `contracts.py`, and `parser.py`, which are still central to the active path.

Finally, read the tests matching the area you are changing. The strongest behavioral contracts are upload cleanup, job parser validation, normalization warnings/confidence, semantic scoring guardrails, orchestration ordering, and explainer fallbacks.

## Operational Notes

The app is started with `python app.py` or `flask --app app:create_app run`. Required dependencies are pinned in `requirements.txt`. `OPENAI_API_KEY` is optional for scoring but required for generated explanations. `OPENAI_MODEL` optionally overrides the default explainer model. `MAX_UPLOAD_MB`, `UPLOAD_FOLDER`, and `FLASK_DEBUG` control runtime upload and debug behavior.

Verification commands used by the existing README are:

```bash
venv/bin/python -m compileall -q app.py main.py web pipeline tests
venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v
```

Use the virtual environment command path if `python` is not available globally. In this workspace, `python3` is available, while plain `python` may not be.
