#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / 'scripts/update_suwon_trail_weekly.py'
text = TARGET.read_text(encoding='utf-8')


def replace_once(old: str, new: str, label: str) -> None:
    global text
    if new in text:
        return
    if old not in text:
        raise SystemExit(f'missing marker: {label}')
    text = text.replace(old, new, 1)


replace_once(
    'def compact_route(route: dict[str, Any]) -> dict[str, Any]:\n    return {key: value for key, value in route.items() if key not in {"latitude", "longitude", "heatExposure", "wetSensitivity"}}\n',
    '''def safety_assessment(route: dict[str, Any], day: dict[str, Any]) -> dict[str, Any]:
    flags: list[str] = []
    severity = 0
    code = int(day["weatherCode"])
    rain_prob = float(day["precipitationProbabilityPct"])
    rain_mm = float(day["precipitationMm"])
    gust = float(day["gustKph"])
    apparent = float(day["apparentMaxC"])
    uv = float(day["uvIndex"])

    if code in (95, 96, 99):
        flags.append("뇌우 가능성")
        severity = max(severity, 3)
    if rain_prob >= 70 or rain_mm >= 10:
        flags.append("강수 부담 큼")
        severity = max(severity, 3)
    elif rain_prob >= 50 or rain_mm >= 3:
        flags.append("젖은 노면 주의")
        severity = max(severity, 2)
    if gust >= 45:
        flags.append("능선 강풍 위험")
        severity = max(severity, 3)
    elif gust >= 35:
        flags.append("돌풍 주의")
        severity = max(severity, 2)
    if apparent >= 35:
        flags.append("체감 폭염")
        severity = max(severity, 3)
    elif apparent >= 31:
        flags.append("더위 대비")
        severity = max(severity, 2)
    if uv >= 8:
        flags.append("자외선 매우 강함")
        severity = max(severity, 2)
    if float(route["wetSensitivity"]) >= 0.9 and rain_mm >= 1:
        flags.append("암릉·바위 미끄럼")
        severity = max(severity, 3)

    labels = ["양호", "주의", "경계", "위험"]
    if apparent >= 31:
        recommended_start = "05:30"
    elif float(route["distanceKm"]) >= 16:
        recommended_start = "06:00"
    else:
        recommended_start = "06:30"

    return {
        "level": labels[severity],
        "levelCode": severity,
        "flags": flags or ["예보상 큰 위험요소 없음"],
        "recommendedStart": recommended_start,
        "sunset": day.get("sunset", ""),
        "officialCheckRequired": True,
    }


def route_provenance(route: dict[str, Any]) -> dict[str, Any]:
    # The app must never present an inferred elevation line as an actual GPX track.
    # gpxUrl is intentionally null until an exact public/owned track is verified.
    query = f"{route['name']} {route['area']}"
    return {
        "profileQuality": "estimated",
        "profileQualityLabel": "고저도 추정 · GPX 미검증",
        "gpxVerified": False,
        "gpxUrl": None,
        "mapQuery": query,
        "verificationDate": None,
    }


def compact_route(route: dict[str, Any]) -> dict[str, Any]:
    compact = {key: value for key, value in route.items() if key not in {"latitude", "longitude", "heatExposure", "wetSensitivity"}}
    compact.update(route_provenance(route))
    return compact
''',
    'safety and provenance helpers',
)

replace_once(
    '            day.update({"score": score, "reasons": reasons, "advice": advice})\n',
    '            day.update({"score": score, "reasons": reasons, "advice": advice, "safety": safety_assessment(route, day)})\n',
    'per-day safety',
)

replace_once(
    '        "schemaVersion": 1,\n',
    '        "schemaVersion": 2,\n',
    'schema version',
)

replace_once(
    '        "source": {\n            "name": "Open-Meteo Forecast API",\n            "url": "https://open-meteo.com/en/docs",\n            "note": "공개 예보와 고정 코스 메타데이터만 사용하며 개인 운동 데이터는 사용하지 않아요.",\n        },\n',
    '''        "source": {
            "name": "Open-Meteo Forecast API",
            "url": "https://open-meteo.com/en/docs",
            "note": "공개 예보와 고정 코스 메타데이터만 사용하며 개인 운동 데이터는 사용하지 않아요.",
        },
        "officialChecks": {
            "weatherWarnings": "https://www.weather.go.kr/",
            "forestFireRisk": "https://fgis.forest.go.kr/",
            "note": "앱의 안전 경고는 예보값 기반 보조 정보입니다. 기상특보·산불·입산통제는 출발 직전에 공식 정보를 다시 확인하세요.",
        },
''',
    'official safety checks',
)

replace_once(
    '    if snapshot.get("schemaVersion") != 1:\n        raise RuntimeError("schemaVersion must be 1")\n',
    '    if snapshot.get("schemaVersion") != 2:\n        raise RuntimeError("schemaVersion must be 2")\n',
    'schema validation',
)

TARGET.write_text(text, encoding='utf-8')
print('v0.10.0 weekly safety/provenance patch applied')
