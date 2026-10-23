# Wind Forecast Portal: Phase Plan

Scope: only what the assignment document asks for. Video, GitHub repo creation and the submission form are handled separately.

**Goal:** a web app (React + Python, Docker, deployed on Vercel) that helps a UK day-ahead buying team (1) see the latest wind forecast available at decision time and (2) quantify forecast accuracy, using Elexon national wind data only (FUELHH actuals, WINDFOR forecasts) for purchase decisions made in January 2026.

**Budget:** 16 hours maximum.

## Confirmed decisions

- **Latest forecast at decision time:** for each target half-hour on delivery day D, use the forecast with the greatest `publishTime` at or before a cutoff on D-1. Default cutoff 09:00 UK time, adjustable in the UI.
- **Data:** fetch January 2026 once, commit a compact snapshot, serve from it. A refresh script re-fetches from Elexon. No live Elexon calls at request time.
- **Frontend:** Vite + React + TypeScript + Recharts.
- **Metrics:** MAE, RMSE, bias (forecast minus actual), in MW.

## Assumptions (to state in README)

- Decisions in January 2026 means decision dates 1 to 31 Jan, so delivery days are 2 Jan to 1 Feb.
- Half-hours with no eligible forecast are excluded from metrics, and the excluded count is shown.
- Timestamps stored in UTC; cutoff interpreted in Europe/London.

---

## Phase 0: Verify data contract (~1h)

- Confirm the exact FUELHH and WINDFOR stream endpoints, query parameter names, date-range limits and response fields in the official Elexon docs.
- Run one real fetch and inspect January data: row counts, duplicates, gaps, forecast horizon, publish frequency, file size.
- **Output:** confirmed field names, size estimate, snapshot format choice.
- **Note:** the Claude sandbox cannot reach Elexon (network allowlist), so this first fetch must run on your machine.

## Phase 1: Scaffold and tooling (~1.5h)

- Backend: FastAPI, pytest + pytest-cov, ruff, mypy (strict), pinned requirements.
- Frontend: Vite TypeScript, ESLint, Prettier, Vitest + Testing Library.
- Shared: `.gitignore`, `.editorconfig`, `.env.example`, optional small CI workflow (lint, type-check, test).
- **Done when:** both projects build and run an empty test suite cleanly.

## Phase 2: Data ingestion (~2h)

- `scripts/fetch_data.py`: fixed base URL, timeouts, retries, schema validation, filter `fuelType == WIND`, deduplicate, write snapshot.
- Commit the snapshot; `repository.py` loads it once at startup.
- **Done when:** snapshot covers 2 Jan to 1 Feb actuals and the matching forecasts, and loads into typed records.

## Phase 3: Domain logic, test-first (~2.5h)

- `selection.py`: latest-publish-at-or-before-cutoff per target time, D-1 cutoff computed in Europe/London.
- `metrics.py`: MAE, RMSE, bias; daily aggregation; exclusion counts.
- Tests: no eligible forecast, exact-boundary publish time, multiple publishes, DST-safe conversion, empty input, hand-computed metric values.
- **Done when:** domain coverage at least 90% and hand-checked numbers match.

## Phase 4: API layer (~1.5h)

- `GET /api/health`
- `GET /api/meta`: valid date range, default cutoff
- `GET /api/forecast?delivery_date=&cutoff=`: per half-hour forecast, publish time, actual (null if absent)
- `GET /api/accuracy?start=&end=&cutoff=`: MAE, RMSE, bias, point count, excluded count, per-day series
- Pydantic validation, consistent error responses, CORS allowlist, security headers.
- **Done when:** TestClient tests cover happy paths and validation failures.

## Phase 5: Frontend (~3h)

- Controls: delivery date picker, cutoff time input.
- Forecast view: forecast line with actuals overlaid, plus which publish time fed it.
- Accuracy view: MAE, RMSE, bias cards, per-day error chart, excluded count, plain-language reading of the numbers.
- Loading, error and empty states; accessible labels; API base URL from env.
- Component and hook tests.
- **Done when:** changing date or cutoff updates charts and metrics end to end.

## Phase 6: Docker (~1h)

- Multi-stage images, non-root user, slim base, `.dockerignore`.
- `docker-compose up` runs the full app locally.

## Phase 7: Vercel deploy (~1.5h)

- Single project: Vite static build plus Python serverless function from `api/index.py`, routed by `vercel.json`.
- Confirm the snapshot fits the function size limit; smoke-test the live URL in incognito.

## Phase 8: Quality pass and README (~1.5h)

- README: file and directory guide, how to start (Docker and non-Docker), Vercel link, explicit AI-tools disclosure, assumptions, how to refresh data.
- Final lint, type-check, coverage run, dependency audit.

**Total: ~15.5h.** If time runs short, protect Phases 3 to 5.

---

## Code quality targets

| Factor | How it is met |
|---|---|
| Maintainability | Layered structure, single-responsibility modules, one config module |
| Complexity | Small pure functions, ruff complexity cap (8) |
| Coupling | Routes call pure domain functions; repository is the only data touchpoint; one frontend API client |
| Duplication | One place defines the selection rule; shared time and chart helpers |
| Test coverage | pytest + Vitest; at least 90% on domain and API, 80% overall |
| Readability | Full type hints and TS types, descriptive names, docstrings on domain rules |
| Security | Input validation, CORS allowlist, security headers, no secrets, fixed fetch URL, non-root containers, pinned deps, `pip-audit` and `npm audit` |
| Standards compliance | ruff + mypy, ESLint + Prettier, ISO 8601 timestamps, RESTful read-only endpoints, semantic HTML |

## Out of scope

Video, repo creation, form submission, other fuel types or data sources, price or demand data, forecasting models, authentication, a database, user accounts, export features, anything beyond the two stated purposes.

## Status

Phase 1 is partly started: backend venv, `requirements*.txt`, `pyproject.toml` and the domain files (`models.py`, `selection.py`, `metrics.py`) exist. Nothing is tested yet. Paused pending your go-ahead.