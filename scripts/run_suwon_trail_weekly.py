#!/usr/bin/env python3
"""Run the weekly generator with one batched, retrying Open-Meteo request."""
from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import urllib.parse
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
GENERATOR_PATH = SCRIPT_DIR / "update_suwon_trail_weekly.py"

spec = importlib.util.spec_from_file_location("suwon_weekly_generator", GENERATOR_PATH)
if spec is None or spec.loader is None:
    raise SystemExit("weekly generator module could not be loaded")
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)


def fetch_all_forecasts() -> dict[str, dict[str, Any]]:
    routes = generator.ROUTES
    params = {
        "latitude": ",".join(str(route["latitude"]) for route in routes),
        "longitude": ",".join(str(route["longitude"]) for route in routes),
        "daily": ",".join(generator.DAILY_FIELDS),
        "timezone": "Asia/Seoul",
        "forecast_days": 16,
    }
    url = f"{generator.OPEN_METEO_URL}?{urllib.parse.urlencode(params)}"
    completed = subprocess.run(
        [
            "curl",
            "--fail",
            "--silent",
            "--show-error",
            "--location",
            "--retry",
            "5",
            "--retry-delay",
            "5",
            "--retry-all-errors",
            "--connect-timeout",
            "20",
            "--max-time",
            "120",
            "--user-agent",
            "SuwonTrailWeeklyPlanner/1.1 (+https://github.com/lsh9955/test)",
            url,
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(completed.stdout)
    items = payload if isinstance(payload, list) else [payload]
    if len(items) != len(routes):
        raise RuntimeError(f"forecast location count mismatch: expected {len(routes)}, got {len(items)}")
    result: dict[str, dict[str, Any]] = {}
    for route, item in zip(routes, items, strict=True):
        daily = item.get("daily") if isinstance(item, dict) else None
        if not isinstance(daily, dict) or not daily.get("time"):
            raise RuntimeError(f"daily forecast missing for {route['id']}")
        result[route["id"]] = daily
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="suwon-trail/weekly.json")
    args = parser.parse_args()

    forecasts = fetch_all_forecasts()
    generator.request_forecast = lambda route: forecasts[route["id"]]
    snapshot = generator.generate()
    generator.validate(snapshot)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {output} with {len(snapshot['routes'])} routes from one batched request")


if __name__ == "__main__":
    main()
