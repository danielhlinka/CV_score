# Review Status

This file tracks completed review findings, fixes, and verification.

Issue 1: `requirements.txt` was polluted and incorrectly encoded.
Plan item 1 [x] Inspect requirements diff and identify noise versus required runtime dependencies.
Plan item 2 [x] Replace requirements with a minimal direct dependency set used by the app.
Plan item 4 [x] Verify encoding, dependency coverage, and resulting git diff.
Review notes: `requirements.txt` had UTF-16 encoding and previously contained environment-specific noise. It is now UTF-8 and limited to direct runtime dependencies imported by this project.
Verification: requirements and gitignore are ASCII text, README remains UTF-8, and static import inspection matches the dependency list in requirements.txt.

Issue 2: virtual environment workflow was not properly enforced.
Plan item 3 [x] Enforce virtual environment workflow and ignore local env directories.
Review notes: virtual environment hygiene was incomplete. The repository now documents `.venv` creation in README and ignores both `.venv/` and `venv/` in `.gitignore`.

Issue 3: CV upload crashed on missing upload directory.
Review notes (new): CV upload failed immediately with `FileNotFoundError: [Errno 2] No such file or directory: 'upload/denishlinka-202608.pdf'` when uploading from local disk.
Plan item 5 [x] Reproduce failure path from code and identify root cause.
Plan item 6 [x] Fix upload path handling so missing directory cannot break upload.
Plan item 7 [x] Verify patch correctness in code and resulting diff.
Fix notes: `app.py` saved files to a relative `upload/` path without creating the directory first. The app now resolves an absolute upload directory under project root and creates it on startup (`os.makedirs(..., exist_ok=True)`).

Issue 4: temporary LLM provider/key mismatch for explainer.
Review notes: OpenAI key is unavailable, but Anthropic key is available. Explainer needs to use `ANTHROPIC_API_KEY` and default to Sonnet (not Opus).
Plan item 8 [x] Refactor `pipeline/explainer.py` from OpenAI SDK to Anthropic SDK.
Plan item 9 [x] Set default explainer model to Sonnet and allow env override.
Plan item 10 [x] Update docs and dependencies to reflect Anthropic usage.
Fix notes: explainer now uses `Anthropic(...).messages.create(...)` with default model `claude-sonnet-4-6` and supports override via `ANTHROPIC_MODEL`.
Revert marker: `[TEMPORARY-REVERT]` This provider switch is temporary and should be reverted when a valid OpenAI key is available again.
Plan item 11 [x] Revert `requirements.txt` from `anthropic==0.100.0` back to `openai==2.34.0`.
Plan item 12 [x] Revert `pipeline/explainer.py` from `ANTHROPIC_API_KEY`/`Anthropic` back to `OPENAI_API_KEY`/`OpenAI`.
Plan item 13 [x] Revert `README.md` references from Anthropic/Sonnet back to OpenAI model/key documentation.
Fix notes: reverted provider dependency and runtime wiring to OpenAI only (`openai==2.34.0`, `OPENAI_API_KEY`, `OPENAI_MODEL` default `gpt-4o-mini`) while keeping robust non-leaking exception handling in explainer.
Verification: `python -m py_compile pipeline/explainer.py app.py` passed, `import openai` succeeds (`2.34.0`), `from app import create_app` succeeds, and README no longer contains Anthropic/Sonnet references.
Plan item 14[x] Review pointless ci.yml. CI/CD is not required nor needed for this project.
Fix notes: removed `.github/workflows/ci.yml` and removed the `CI / test gate` README section to keep docs aligned with local-only workflow.
Verification: `.github/workflows` contains no workflow files and `README.md` has no `CI / test gate`, `compileall`, or `unittest discover` CI gate references.
Plan item 15[x] Review code structure and code architecture.
Plan item 16[x] Comment and document the solution in a clear and concise manner. Edit README.md with any necessary instructions or explanations for future developers or users of the code.
Plan item 17 [x] Modularize the codebase to improve maintainability and readability. Ensure that related functionalities are grouped together in appropriate modules and classes. Object-oriented design principles should be applied where suitable to enhance code organization and reusability according to Python best practices.
Issue 5: parser/scoring pipeline produced misleading outputs on arbitrary CV layouts.
Review notes: section-template assumptions and date parsing fragility caused false `0 year(s)` and intern-like outcomes when extraction quality dropped.
Plan item 14 [x] Add full-text normalization stage that creates evaluator-ready structured input with confidence metadata.
Plan item 15 [x] Refactor parser/enricher to use normalized fields first and derive embeddings only from normalized snippets.
Plan item 16 [x] Add scoring guardrails so low-confidence parsing does not hard-collapse to zero experience or forced role penalties.
Plan item 17 [x] Surface parser confidence and warnings in output and sanity logs.
Plan item 18 [x] Verify behavior on `CV_DENIS_HLINKA.pdf` plus static compile checks.
Plan item 19 [x] Exclude education timeline ranges from experience-year aggregation in full-text parser.
Plan item 20 [x] Improve skill extraction for modern data stack terms so CV terms like Databricks/PySpark map to requested skill `spark`.
Fix notes: introduced `pipeline/normalizer.py`, wired `parse_cv -> normalized object -> enrich_cv -> match`, and added parser-confidence aware scoring.
Fix notes (education filter): experience parser now excludes date ranges with education context unless clear work context exists, preventing education periods from inflating work years.
Verification: parser-only run on `CV_DENIS_HLINKA.pdf` now reports `experience_years=6.67`, `jobs_detected=5`, `parser_confidence=high`. End-to-end scoring script no longer collapses experience to zero and produced `final_score=0.875` for the same job input profile.
Verification notes: embedding loading is now lazy and resilient. If `all-MiniLM-L6-v2` cannot be loaded (network/cache issue), deterministic hash fallback is used instead of crashing at import.
Verification notes (skills): with required skills `docker, python, spark, snowflake, cloud, architecture`, extracted CV skills now include all six canonicals and `skills` score is `1.0`.

Issue 6: security/resilience hardening and pythonic error handling based on dual code review.
Review notes: two parallel subagent reviews flagged critical risks (unsanitized markdown XSS sink, hardcoded debug mode, weak upload validation/error paths, and role taxonomy inconsistency).
Plan item 21 [x] Delegate parallel implementation to two subagents: backend hardening + frontend XSS/UX fixes.
Plan item 22 [x] Implement strict upload request validation with explicit HTTP errors and env-driven upload size limit.
Plan item 23 [x] Implement safer runtime behavior: debug mode controlled by `FLASK_DEBUG`, not hardcoded.
Plan item 24 [x] Add HTML-safe error rendering for browser form flow while preserving JSON error responses for non-HTML clients.
Plan item 25 [x] Ensure uploaded CV files are deleted after text extraction to reduce retention risk.
Plan item 26 [x] Sanitize markdown output with DOMPurify before assigning to `innerHTML`.
Plan item 27 [x] Fix submit button loading bug in index template.
Plan item 28 [x] Align role taxonomy by adding `management` support in role templates/signals.
Plan item 29 [x] Tighten pythonic validation in `job_parser` (`years_required` parsing and explicit bad input handling).
Plan item 30 [x] Replace raw exception leakage in explainer with server logging + generic user-safe message.
Fix notes: backend hardening is implemented in `app.py` and `pipeline/job_parser.py`; frontend sanitation/UX fixes are in `templates/results.html` and `templates/index.html`.
Verification: `py_compile` passed for modified Python modules. Flask test client checks confirm `400` for missing file, `400` for invalid years input, `415` for unsupported extension, and `200` for valid request. Upload directory contents remain unchanged after successful scoring request (temporary saved file is deleted).

Issue 7: structural quality refactor after review round (approved subset execution).
Review notes: user approved item 2, 3, 4, 5, 6.1, and 7 from the proposed plan; item 1 was explicitly dropped as not needed for local use; item 6.2 and 6.3 were explicitly rejected.
Plan item 31 [x] Record approved scope and run implementation step-by-step with subagent delegation on disjoint file ownership.
Plan item 32 [x] Refactor Flask entrypoint to an application factory with centralized config loading and safe defaults.
Plan item 33 [x] Introduce typed contracts for core pipeline payloads and apply them to parser/enricher/matcher boundaries.
Plan item 34 [x] Centralize taxonomy constants (roles/seniority/education) and remove duplicate local definitions across modules.
Plan item 35 [x] Remove stale/unused code paths with minimal behavioral impact and no regression to current scoring flow.
Plan item 36 [x] Add only 2-3 highest-value automated tests (6.1 scope only).
Plan item 37 [x] Add a minimal CI quality gate that runs compile checks and tests.
Plan item 38 [x] Verify end-to-end behavior and update this file with concise review findings.
Fix notes: delegated implementation to four subagents with disjoint ownership (app factory/config, typed contracts + taxonomy + cleanup, tests, CI), then integrated and re-verified locally.
Fix notes (app/runtime): `app.py` now uses `create_app(...)`, centralizes runtime config (`UPLOAD_FOLDER`, `MAX_CONTENT_LENGTH`, `RUN_DEBUG`), and preserves existing validation/error behavior; `main.py` now reuses configured app entrypoint.
Fix notes (typing/taxonomy): `pipeline/__init__.py` now holds shared role/seniority/education constants and TypedDict contracts (`NormalizedCV`, `ParsedCV`, `EnrichedCV`, `JobProfile`, `MatchResult`); parser/enricher/matcher/job parser signatures were aligned.
Fix notes (cleanup): removed stale legacy experience parsing paths from `pipeline/experience.py` and fixed `pipeline/sanity_check.py` seniority validation to use canonical `VALID_SENIORITY`.
Fix notes (tests + CI): added `tests/test_core_behavior.py` with exactly 3 high-value tests and added `.github/workflows/ci.yml` compile+test gate.
Verification: `python -m py_compile` passed for touched modules. `python -m compileall -q app.py main.py pipeline tests` passed. `python -m unittest discover -s tests -p 'test_*.py' -v` passed (3/3). Parser/enricher/matcher smoke run still returns `score=1.0`, `skills=1.0`, `years=7.33`, `role=data` for representative Data Architect input.

Issue 8: item 15 major architecture refactor with strict behavior preservation.
Review notes: this refactor will prioritize functional parity first, then code quality and maintainability improvements aligned with Python/Flask best practices from official docs.
Plan item 39 [x] Define refactor boundaries and preserve-or-improve invariants for `/score` flow, parser normalization, and scoring outputs.
Plan item 40 [x] Delegate parallel implementation to subagents with disjoint ownership and integrate without cross-file regressions.
Plan item 41 [x] Refactor web layer to blueprint-based structure and centralized error-handler registration while preserving response contracts.
Plan item 42 [x] Refactor pipeline internals (normalizer decomposition and semantic scoring helpers/caches) for readability, testability, and lower duplication.
Plan item 43 [x] Add regression tests that lock critical behavior before/after refactor (upload lifecycle, score schema, parser confidence/warnings shape).
Plan item 44 [x] Execute full verification (compileall + unittest + targeted runtime smoke) and compare outputs for representative CV/job profiles.
Plan item 45 [x] Complete item 16 documentation updates in README and add concise review notes to this file.
Fix notes: delegated three parallel subagents with disjoint ownership and integrated all outputs after local review.
Fix notes (web architecture): introduced `web/` package with centralized runtime config, blueprint-based routes, and unified error handler registration while preserving app-factory semantics.
Fix notes (pipeline quality): decomposed `pipeline/normalizer.py` into typed helper units and added `pipeline/semantic.py` for shared cosine helpers and memoized embedding reuse across `embedder.py` and `matcher.py`.
Fix notes (tests): expanded regression coverage to 12 tests spanning upload lifecycle, HTTP contract behavior, normalizer confidence/warnings shape, and semantic scoring/cache stability.
Verification: `venv/bin/python -m compileall -q app.py main.py web pipeline tests` passed.
Verification: `venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v` passed (12/12).
Verification: representative CV smoke run still returns identical metrics (`final_score=1.0`, `skills=1.0`, `seniority=1.0`, `experience=1.0`, `role=data`, `years=6.67`, `parser_confidence=high`, `warnings=1`).

Issue 9: item 17 codebase reorganization with strict behavior preservation.
Review notes: this phase will modularize orchestration concerns into focused components, keep HTTP/score contracts stable, and apply Python/Flask best practices grounded in official docs.
Plan item 46 [x] Lock invariants for `/score` request contract, upload cleanup semantics, score payload shape, and existing parser/scoring outputs.
Plan item 47 [x] Delegate parallel subagents for disjoint module ownership (scoring orchestration service, upload lifecycle component, explainer OOP refactor) and integrate reviewed outputs.
Plan item 48 [x] Reorganize web layer to consume dedicated service classes/modules (no behavior change to route responses or status codes).
Plan item 49 [x] Preserve backward-compatible public interfaces where used by existing templates/tests (`create_app`, `explain`, scoring result shape).
Plan item 50 [x] Expand regression tests for reorganized modules and preserve current end-to-end coverage.
Plan item 51 [x] Run full verification (`compileall`, unittest suite, representative CV smoke) and compare outputs to pre-refactor baseline.
Plan item 52 [x] Document item 17 completion and concise lessons in this file and update `tasks/lessons.md` if a repeatable pattern is identified.
Fix notes: delegated three parallel subagents with disjoint ownership and integrated all outputs after mainline review.
Fix notes (modularization): introduced `web/scoring_service.py` (class-based orchestrator with dependency injection), `web/uploads.py` (class-based upload validation/staging/cleanup), and refactored `web/routes.py` to consume both modules directly.
Fix notes (explainer OOP): `pipeline/explainer.py` now uses `OpenAIExplainer` while preserving public `explain(result)` compatibility and existing fallback messages.
Fix notes (compatibility): preserved route contracts, status codes, error texts, `create_app` entrypoint, and scoring result/explanation payload shape.
Fix notes (tests): added targeted regression tests `tests/test_scoring_orchestration_service.py`, `tests/test_uploads_behavior.py`, and `tests/test_explainer_behavior.py`.
Verification: `venv/bin/python -m py_compile web/routes.py web/scoring_service.py web/uploads.py pipeline/explainer.py` passed.
Verification: `venv/bin/python -m compileall -q app.py main.py web pipeline tests` passed.
Verification: `venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v` passed (24/24).
Verification: representative CV smoke output remained stable (`final_score=1.0`, `skills=1.0`, `seniority=1.0`, `experience=1.0`, `role=data`, `years=6.67`, `parser_confidence=high`, `warnings=1`).
Lessons: no new user-correction pattern was identified in this cycle, so `tasks/lessons.md` remained unchanged.

Issue 10: pipeline module split by responsibility with backward compatibility.
Review notes: objective is structural reorganization only; functionality and existing contracts remain priority one.
Plan item 53 [x] Define migration map from current `pipeline/*.py` modules to responsibility-based packages (`input`, `normalize`, `enrich`, `score`, `output`, `orchestration`).
Plan item 54 [x] Introduce new package modules and move logic with clear naming while keeping old import paths as compatibility wrappers.
Plan item 55 [x] Split shared contracts/constants into dedicated modules and preserve `pipeline.__init__` exports used by existing code/tests.
Plan item 56 [x] Update internal imports/wiring (including web scoring orchestration) to consume the new module layout without changing runtime behavior.
Plan item 57 [x] Run full verification (`compileall`, full unittest suite, representative CV smoke) and compare key scoring outputs to baseline.
Plan item 58 [x] Document final module map and migration notes in README and this file.
Fix notes: added responsibility-based pipeline packages (`input`, `normalize`, `enrich`, `score`, `output`, `orchestration`) and split core logic accordingly.
Fix notes: introduced `pipeline/constants.py` + `pipeline/contracts.py` and rewired `pipeline/__init__.py` to preserve existing imports.
Fix notes: legacy modules under `pipeline/*.py` now serve as compatibility entrypoints so existing tests/routes/imports keep working.
Fix notes: moved scoring orchestration implementation to `pipeline/orchestration/scoring_pipeline.py`; `web/scoring_service.py` now wraps it.
Verification: `venv/bin/python -m py_compile` passed for updated pipeline/web modules.
Verification: `venv/bin/python -m compileall -q app.py main.py web pipeline tests` passed.
Verification: `venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v` passed (24/24).
Verification: representative CV smoke output remains unchanged (`final_score=1.0`, `skills=1.0`, `seniority=1.0`, `experience=1.0`, `role=data`, `years=6.67`, `parser_confidence=high`, `warnings=1`).
