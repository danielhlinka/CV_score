# 🐍 Python-Specific Prompts

> **Optional supplement.** Use these alongside the generic prompts in this directory.
> These target Python/FastAPI-specific patterns, anti-patterns, and best practices.

---

## 1. Python Code Review — Deep Dive

```
@workspace Review the following Python code with a focus on Python-specific best practices:

File(s): [FILE_PATH]

Check for:

**Type Safety & Hints:**
- All functions have complete type hints (params + return)
- Complex types use `Optional`, `Union`, `list[T]`, `dict[K,V]` (not bare `list`, `dict`)
- Pydantic models are used for structured data, not raw dicts
- No `Any` type unless explicitly justified

**Async Patterns:**
- async functions actually await something (not sync code wrapped in async)
- No blocking I/O in async functions (no `time.sleep()`, no sync `requests`)
- `httpx.AsyncClient` used instead of `requests` in async code
- Proper use of `asyncio.gather()` for concurrent operations
- Connection pools / clients are reused, not created per-request

**Error Handling:**
- No bare `except:` or `except Exception:` that swallows errors silently
- Specific exception types caught
- `raise ... from e` used to preserve exception chains
- HTTP errors return proper status codes (not 500 for everything)
- Background tasks have error handling (won't crash silently)

**FastAPI Specific:**
- Dependency injection used properly (`Depends()`)
- Path/query params have proper types and validation
- Response models defined (`response_model=`)
- Status codes explicit on endpoints (`status_code=201`)
- Middleware doesn't have performance issues (runs on every request)
- CORS, auth middleware ordered correctly
- No business logic in route handlers — delegated to service layer
- Proper use of `HTTPException` with meaningful detail messages

**Security:**
- No SQL string concatenation — parameterized queries only
- No `eval()`, `exec()`, or `__import__()` on user input
- Secrets loaded from env vars, not hardcoded
- File paths validated (no path traversal)
- Input validated before use (Pydantic, not manual checks)

**Performance:**
- No N+1 queries (fetching in loop vs. batch query)
- Large querysets paginated
- Database connections properly managed (async context managers)
- Expensive operations cached where appropriate
- No synchronous sleep or blocking calls in async handlers

**Python Idioms:**
- List/dict comprehensions used where appropriate (not overcomplicated)
- Context managers (`with`) for resource management
- `pathlib.Path` preferred over `os.path`
- f-strings preferred over `.format()` or `%`
- `dataclasses` or Pydantic models instead of plain dicts for structured data
- `enum.Enum` for fixed sets of values

For each issue found, provide:
1. The specific line
2. What's wrong (with Python-specific explanation)
3. The corrected code
```

---

## 2. Python Debugging — Common Pitfalls

```
@workspace I'm seeing this error in my Python code:

```
[PASTE ERROR / TRACEBACK HERE]
```

File(s) involved: [FILE_PATH]

Investigate with special attention to these common Python pitfalls:
- **Mutable default arguments** (`def f(items=[])` — shared across calls)
- **Import circular dependencies** (A imports B, B imports A)
- **Late binding closures** (lambda in loop capturing variable by reference)
- **Async/sync mismatch** (calling sync function in async context or vice versa)
- **Missing `await`** (async function called without await — returns coroutine, not result)
- **Dictionary mutation during iteration**
- **String encoding issues** (bytes vs str)
- **Integer division** (`/` vs `//`)
- **Truthy/falsy gotchas** (`0`, `""`, `[]`, `None` all falsy)
- **PYTHONPATH / import resolution** (module not found despite existing)

Provide the root cause and fix.
```

---

## 3. FastAPI Endpoint Review

```
@workspace Review this FastAPI endpoint for production readiness:

File: [FILE_PATH]
Endpoint: [METHOD] [PATH]

Check against this FastAPI production checklist:

□ Route decorator has explicit `status_code` and `response_model`
□ All path/query/body params have type hints and validation
□ Uses `Depends()` for auth, database, and shared logic
□ Request validation uses Pydantic model (not manual dict parsing)
□ Response uses Pydantic model (not raw dict)
□ Errors return appropriate HTTP status codes with detail message
□ Business logic is in a service function, not in the route handler
□ Database session is properly managed (dependency injection, not manual)
□ External API calls have timeout and error handling
□ Logging includes request context (user ID, request ID)
□ Sensitive data not logged (passwords, tokens, PII)
□ Endpoint is documented (docstring → shows in Swagger)
□ Edge cases handled (empty results, not found, duplicates)
□ If creating/updating: idempotency considered
□ If deleting: soft delete vs hard delete is intentional

Provide specific fixes for any failing checks.
```

---

## 4. Python Dependency & Import Audit

```
@workspace Audit the Python dependencies and imports in this project:

Check:
1. **requirements.txt / pyproject.toml:**
   - All packages pinned to exact versions (not `>=` or unpinned)
   - No unused dependencies (installed but never imported)
   - No missing dependencies (imported but not in requirements)
   - No known security vulnerabilities in current versions
   - Dev dependencies separated from production dependencies

2. **Import hygiene:**
   - No wildcard imports (`from module import *`)
   - No unused imports
   - No circular imports
   - Import order follows convention: stdlib → third-party → local
   - Relative vs absolute imports are consistent

3. **Compatibility:**
   - No features from Python versions newer than what's in production
   - Type hints compatible with the target Python version
   - No deprecated stdlib usage (`distutils`, `imp`, `optparse`, etc.)

List all issues found with specific files and line numbers.
```

---

## 5. Python Testing — Improve Test Quality

```
@workspace Analyze the test suite for this Python project and suggest improvements:

Test directory: [tests/]
Framework: [pytest / unittest]

Check:
1. **Coverage gaps:**
   - Which functions/endpoints have no tests?
   - Which error paths are untested?
   - Are edge cases covered (empty input, None, max values)?

2. **Test quality:**
   - Tests are independent (no shared mutable state between tests)
   - Each test tests ONE thing (clear arrange/act/assert)
   - Test names describe the scenario, not the implementation
   - No hardcoded sleep() — use proper async testing
   - Fixtures used for setup/teardown (not repeated setup code)
   - Mocks are minimal — mock boundaries, not internals

3. **pytest-specific:**
   - `conftest.py` used for shared fixtures
   - Parametrize used for testing multiple inputs
   - Proper markers (`@pytest.mark.slow`, `@pytest.mark.integration`)
   - `tmp_path` / `tmp_path_factory` for file tests
   - `caplog` for testing log output
   - `monkeypatch` preferred over `unittest.mock.patch`

4. **Async testing:**
   - `pytest-asyncio` configured properly
   - Async fixtures use `@pytest_asyncio.fixture`
   - `httpx.AsyncClient` used for testing FastAPI (not `TestClient` for async)

Provide specific test implementations for the top 5 most important missing tests.
```

---

## 6. SQLAlchemy / Database Patterns

```
@workspace Review the database code in this project for SQLAlchemy best practices:

Files: [DATABASE FILES / MODELS]

Check:
1. **Models:**
   - All tables have primary keys defined
   - Foreign keys have proper `ondelete` behavior
   - Indexes on frequently queried columns
   - Column types match the data (no `String` for dates)
   - `__repr__` defined for debugging
   - Relationship `lazy` loading strategy is intentional

2. **Queries:**
   - No N+1 query patterns (use `joinedload` / `selectinload`)
   - Filters use indexed columns
   - Pagination on all list queries
   - `SELECT` only needed columns for large tables
   - No raw SQL unless justified (use ORM)

3. **Session management:**
   - Sessions are scoped properly (per-request in web apps)
   - `commit()` called explicitly, not auto-commit
   - `rollback()` in error handlers
   - Context managers used (`with Session() as session:`)
   - No long-lived sessions

4. **Migrations (Alembic):**
   - All schema changes have migration files
   - Migrations are reversible (have `downgrade()`)
   - Data migrations separated from schema migrations
   - No breaking migrations without deployment plan

List issues with specific files and provide corrected code.
```

---

## 7. Python Performance Optimization

```
@workspace Analyze this Python code for performance issues:

File(s): [FILE_PATH]
Context: [What this code does / expected load]

Look for:
1. **Algorithmic:**
   - O(n²) or worse patterns (nested loops, repeated lookups in lists)
   - Use `set` or `dict` for O(1) lookups instead of list scanning
   - `collections.defaultdict`, `Counter`, `deque` where appropriate

2. **I/O bound:**
   - Sequential API calls that could be `asyncio.gather()`
   - Sequential DB queries that could be batched
   - File operations that could use buffering
   - Missing connection pooling

3. **Memory:**
   - Large lists that could be generators
   - Unnecessary copies of large data structures
   - Accumulating data in memory vs streaming
   - Not closing resources (file handles, connections)

4. **Python-specific:**
   - Global imports of heavy modules that could be lazy
   - Repeated regex compilation (should use `re.compile()`)
   - String concatenation in loops (use `join()`)
   - Repeated attribute access in loops (assign to local variable)

For each issue, provide:
- Current code
- Optimized code  
- Expected performance impact
```

---

## 8. Pydantic Model Audit

```
@workspace Review all Pydantic models in this project:

Files: [SCHEMA FILES]

Check:
1. **Validation:**
   - `Field()` with proper constraints (min_length, ge, le, regex)
   - Custom validators for business rules (`@field_validator`)
   - Model-level validators for cross-field validation (`@model_validator`)
   - Proper use of `Optional` vs required fields
   - Default values make sense

2. **Structure:**
   - Separate models for Create/Update/Response (not one model for everything)
   - Base model inheritance used to avoid duplication
   - `model_config` with `from_attributes = True` for ORM mode
   - Sensitive fields excluded from response models

3. **Naming:**
   - Model names match the domain (not generic `Data`, `Item`)
   - Field names match the API contract (camelCase if API needs it)
   - Consistent naming across models

4. **Documentation:**
   - Fields have `description` in `Field()` (shows in Swagger)
   - `model_config` has `json_schema_extra` with examples
   - Enum fields use proper Python Enums

List all models and flag any issues.