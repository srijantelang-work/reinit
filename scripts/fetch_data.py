"""Fetch January 2026 Elexon wind data and create snapshot.json.

Fetches:
1. FUELHH actuals: 2026-01-02 to 2026-02-01 (filtered to fuelType == "WIND").
2. WINDFOR forecasts: published between 2025-12-30 and 2026-01-31,
   covering delivery targets 2026-01-02 to 2026-02-01.

Deduplicates and saves to data/snapshot.json.
"""

from __future__ import annotations

import json
import logging
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1"
TIMEOUT_SECONDS = 30
MAX_RETRIES = 4
BACKOFF_FACTOR = 1.5

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SNAPSHOT_PATH = DATA_DIR / "snapshot.json"


def fetch_with_retry(endpoint: str, params: dict[str, str]) -> list[dict[str, Any]]:
    """Fetch JSON data from Elexon API with exponential backoff retries."""
    query_str = urllib.parse.urlencode(params)
    url = f"{BASE_URL}/{endpoint}?{query_str}"

    headers = {
        "User-Agent": "WindForecastPortal/1.0 (+https://github.com/srijantelang-work/reinit)",
        "Accept": "application/json",
    }

    last_error: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as response:
                if response.status == 200:
                    parsed = json.loads(response.read().decode("utf-8"))
                    raw_data = parsed.get("data", [])
                    return list(raw_data) if isinstance(raw_data, list) else []
                logger.warning(
                    "Unexpected status %s for %s, attempt %d/%d",
                    response.status,
                    url,
                    attempt,
                    MAX_RETRIES,
                )
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
            last_error = exc
            logger.warning(
                "Fetch error (%s) on %s, attempt %d/%d",
                exc,
                url,
                attempt,
                MAX_RETRIES,
            )
            time.sleep(BACKOFF_FACTOR**attempt)

    raise RuntimeError(f"Failed to fetch {url} after {MAX_RETRIES} attempts: {last_error}")


def fetch_fuelhh_actuals(start_date: date, end_date: date) -> list[dict[str, Any]]:
    """Fetch FUELHH wind generation actuals in 5-day chunks to respect API limits."""
    logger.info("Fetching FUELHH actuals from %s to %s...", start_date, end_date)
    all_actuals: list[dict[str, Any]] = []

    current = start_date
    while current <= end_date:
        chunk_end = min(current + timedelta(days=4), end_date)
        params = {
            "format": "json",
            "settlementDateFrom": current.isoformat(),
            "settlementDateTo": chunk_end.isoformat(),
        }
        logger.info("  Fetching FUELHH chunk: %s to %s", current, chunk_end)
        rows = fetch_with_retry("datasets/FUELHH", params)

        wind_rows = [
            {
                "settlement_date": r["settlementDate"],
                "settlement_period": int(r["settlementPeriod"]),
                "start_time": r["startTime"],
                "publish_time": r["publishTime"],
                "generation_mw": int(r["generation"]),
            }
            for r in rows
            if r.get("fuelType") == "WIND" and r.get("generation") is not None
        ]
        all_actuals.extend(wind_rows)
        current = chunk_end + timedelta(days=1)
        time.sleep(0.3)  # Polite pause between requests

    # Deduplicate by (settlement_date, settlement_period)
    dedup: dict[tuple[str, int], dict[str, Any]] = {}
    for item in all_actuals:
        key = (item["settlement_date"], item["settlement_period"])
        dedup[key] = item

    results = sorted(dedup.values(), key=lambda x: (x["settlement_date"], x["settlement_period"]))
    logger.info("Fetched %d unique FUELHH wind records", len(results))
    return results


def fetch_windfor_forecasts(
    pub_start: datetime, pub_end: datetime, target_min: datetime, target_max: datetime
) -> list[dict[str, Any]]:
    """Fetch WINDFOR wind generation forecasts in 5-day publication chunks."""
    logger.info("Fetching WINDFOR forecasts published from %s to %s...", pub_start, pub_end)
    all_forecasts: list[dict[str, Any]] = []

    current = pub_start
    while current < pub_end:
        chunk_end = min(current + timedelta(days=5), pub_end)
        params = {
            "format": "json",
            "publishDateTimeFrom": current.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "publishDateTimeTo": chunk_end.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        logger.info("  Fetching WINDFOR chunk: %s to %s", current, chunk_end)
        rows = fetch_with_retry("datasets/WINDFOR", params)

        for r in rows:
            gen = r.get("generation")
            if gen is None:
                continue
            st = datetime.fromisoformat(r["startTime"].replace("Z", "+00:00"))
            if target_min <= st <= target_max:
                all_forecasts.append(
                    {
                        "start_time": r["startTime"],
                        "publish_time": r["publishTime"],
                        "generation_mw": int(gen),
                    }
                )

        current = chunk_end
        time.sleep(0.3)

    # Deduplicate by (publish_time, start_time)
    dedup: dict[tuple[str, str], dict[str, Any]] = {}
    for item in all_forecasts:
        key = (item["publish_time"], item["start_time"])
        dedup[key] = item

    results = sorted(dedup.values(), key=lambda x: (x["publish_time"], x["start_time"]))
    logger.info("Fetched %d unique WINDFOR records covering target window", len(results))
    return results


def main() -> None:
    """Run data ingestion and produce snapshot.json."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Actuals range: delivery days 2026-01-02 to 2026-02-01
    act_start = date(2026, 1, 2)
    act_end = date(2026, 2, 1)

    actuals = fetch_fuelhh_actuals(act_start, act_end)

    # Forecast publication window: 2025-12-30 to 2026-01-31 23:59:59
    pub_start = datetime(2025, 12, 30, 0, 0, 0, tzinfo=timezone.utc)
    pub_end = datetime(2026, 2, 1, 0, 0, 0, tzinfo=timezone.utc)

    # Delivery targets of interest
    target_min = datetime(2026, 1, 2, 0, 0, 0, tzinfo=timezone.utc)
    target_max = datetime(2026, 2, 1, 23, 30, 0, tzinfo=timezone.utc)

    forecasts = fetch_windfor_forecasts(pub_start, pub_end, target_min, target_max)

    snapshot_data = {
        "metadata": {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "actuals_count": len(actuals),
            "forecasts_count": len(forecasts),
            "delivery_date_range": [act_start.isoformat(), act_end.isoformat()],
        },
        "actuals": actuals,
        "forecasts": forecasts,
    }

    with open(SNAPSHOT_PATH, "w", encoding="utf-8") as f:
        json.dump(snapshot_data, f, indent=2)

    file_size_mb = SNAPSHOT_PATH.stat().st_size / (1024 * 1024)
    logger.info(
        "Saved snapshot to %s: %d actuals, %d forecasts (%.2f MB)",
        SNAPSHOT_PATH,
        len(actuals),
        len(forecasts),
        file_size_mb,
    )


if __name__ == "__main__":
    main()
