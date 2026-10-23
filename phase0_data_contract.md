# Phase 0 Output: Elexon Data Contract

**Verified on:** 2026-10-23 via live API calls.

## Base URL

```
https://data.elexon.co.uk/bmrs/api/v1
```

No API key required (public endpoints).

## FUELHH — Half-Hourly Generation Outturn by Fuel Type

**Endpoint:** `GET /datasets/FUELHH`

**Query parameters:**

| Parameter            | Type   | Notes                                |
|----------------------|--------|--------------------------------------|
| `format`             | string | `json`, `csv`, or `xml`              |
| `settlementDateFrom` | date   | `YYYY-MM-DD`                         |
| `settlementDateTo`   | date   | `YYYY-MM-DD`                         |
| `settlementPeriod`   | int[]  | 1–48 (50 on clock-change days)       |

**Response fields (per row):**

| Field              | Type     | Example                        |
|--------------------|----------|--------------------------------|
| `dataset`          | string   | `"FUELHH"`                     |
| `publishTime`      | datetime | `"2026-01-02T00:30:00Z"`      |
| `startTime`        | datetime | `"2026-01-02T00:00:00Z"`      |
| `settlementDate`   | date     | `"2026-01-02"`                 |
| `settlementPeriod` | int      | `1`                            |
| `fuelType`         | string   | `"WIND"`, `"CCGT"`, etc.      |
| `generation`       | int (MW) | `15228`                        |

**Filter needed:** `fuelType == "WIND"` to get wind actuals.

One response for SP 1 on 2026-01-02 returned **20 fuel types** (BIOMASS, CCGT, COAL, INTELEC, INTEW, INTFR, INTGRNL, INTIFA2, INTIRL, INTNED, INTNEM, INTNSL, INTVKL, NPSHYD, NUCLEAR, OCGT, OIL, OTHER, PS, WIND).

## WINDFOR — Wind Generation Forecast

**Endpoint:** `GET /datasets/WINDFOR`

**Query parameters:**

| Parameter            | Type   | Notes                                |
|----------------------|--------|--------------------------------------|
| `format`             | string | `json`, `csv`, or `xml`              |
| `settlementDateFrom` | date   | `YYYY-MM-DD` (maps to target period) |
| `settlementDateTo`   | date   | `YYYY-MM-DD`                         |
| `settlementPeriod`   | int[]  | 1–48                                 |

**Response fields (per row):**

| Field         | Type     | Example                        |
|---------------|----------|--------------------------------|
| `dataset`     | string   | `"WINDFOR"`                    |
| `publishTime` | datetime | `"2026-10-23T12:30:00Z"`      |
| `startTime`   | datetime | `"2026-10-23T00:00:00Z"`      |
| `generation`  | int (MW) | `10093`                        |

**Key differences from FUELHH:**
- No `settlementDate` or `settlementPeriod` fields — uses `startTime` only.
- `startTime` is **hourly** (not half-hourly).
- Forecasts are published ~8 times/day (03:30, 05:30, 08:30, 10:30, 12:30, 16:30, 19:30, 23:30 UTC).
- Coverage spans D-0 20:00 to D+2 20:00 per publish.

## Size Estimate

- FUELHH: ~20 fuel types × 48 SPs × 31 days ≈ 29,760 rows total; filtering to WIND only ≈ 1,488 rows.
- WINDFOR: ~8 publishes/day × ~72 hours of forecast × 31 days ≈ ~17,856 rows.
- Combined JSON snapshot (WIND-only actuals + all forecasts): estimated **< 3 MB**.

## Snapshot Format Choice

**JSON** — two arrays (`actuals` and `forecasts`) in a single file `data/snapshot.json`. Compact, easy to load in both Python and TypeScript, well under Vercel's function size limit.
