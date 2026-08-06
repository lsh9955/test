#!/usr/bin/env python3
"""Build the public weekly Suwon trail recommendation snapshot.

The output contains only public route metadata and public weather forecasts.
No app, Samsung Health, GPS, or user data is read.
"""
from __future__ import annotations

import argparse
import json
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

KST = timezone(timedelta(hours=9))
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
DAILY_FIELDS = [
    "weather_code",
    "temperature_2m_max",
    "temperature_2m_min",
    "apparent_temperature_max",
    "precipitation_sum",
    "precipitation_probability_max",
    "wind_speed_10m_max",
    "wind_gusts_10m_max",
    "uv_index_max",
    "sunrise",
    "sunset",
]

ROUTES: list[dict[str, Any]] = [
    {
        "id": "gwanggyo-brothers",
        "name": "광교산 형제봉 왕복",
        "area": "수원·광교",
        "latitude": 37.3227,
        "longitude": 127.0340,
        "distanceKm": 8.2,
        "ascentM": 520,
        "duration": "2시간 30분~3시간 30분",
        "difficulty": "중",
        "surface": "흙길·돌계단·능선",
        "transport": "광교산입구·경기대 방면 접근",
        "bac": "블랙야크 100대 명산 인증 지점은 시루봉",
        "summary": "수원에서 접근이 쉽고 짧게 강도를 내기 좋은 대표 코스",
        "caution": "비 뒤 돌계단과 뿌리 구간이 미끄러울 수 있어요.",
        "heatExposure": 0.55,
        "wetSensitivity": 0.75,
    },
    {
        "id": "gwanggyo-sirubong",
        "name": "광교산 시루봉 종주",
        "area": "수원·용인",
        "latitude": 37.3449,
        "longitude": 127.0225,
        "distanceKm": 13.5,
        "ascentM": 850,
        "duration": "4시간~5시간 30분",
        "difficulty": "중상",
        "surface": "능선·계단·흙길",
        "transport": "경기대 또는 광교산입구 출발",
        "bac": "블랙야크 100대 명산",
        "summary": "형제봉과 시루봉을 이어 달리는 수원 대표 장거리 능선",
        "caution": "더운 날에는 후반 급격히 체력이 떨어질 수 있어요.",
        "heatExposure": 0.72,
        "wetSensitivity": 0.78,
    },
    {
        "id": "baragwanggyo",
        "name": "바라산·백운산·광교산 연계",
        "area": "의왕·수원",
        "latitude": 37.3636,
        "longitude": 127.0035,
        "distanceKm": 18.8,
        "ascentM": 1250,
        "duration": "5시간 30분~7시간",
        "difficulty": "상",
        "surface": "긴 능선·급경사·흙길",
        "transport": "바라산 자연휴양림·백운호수 방면",
        "bac": "광교산 시루봉은 블랙야크 100대 명산",
        "summary": "긴 오르내림과 누적 상승을 훈련하기 좋은 종주 코스",
        "caution": "우천·폭염·강풍 예보에는 짧은 코스로 줄이는 편이 안전해요.",
        "heatExposure": 0.9,
        "wetSensitivity": 0.9,
    },
    {
        "id": "chilbo-ridge",
        "name": "칠보산 능선 순환",
        "area": "수원·화성",
        "latitude": 37.2577,
        "longitude": 126.9396,
        "distanceKm": 9.6,
        "ascentM": 430,
        "duration": "2시간 30분~4시간",
        "difficulty": "중",
        "surface": "완만한 능선·흙길",
        "transport": "호매실·칠보산 입구 방면",
        "bac": "블랙야크 100대 명산 해당 없음",
        "summary": "수원 서부에서 짧은 업다운을 반복하기 좋은 숲길",
        "caution": "갈림길이 많아 GPX 확인이 도움이 돼요.",
        "heatExposure": 0.45,
        "wetSensitivity": 0.62,
    },
    {
        "id": "surisan-loop",
        "name": "수리산 태을봉·슬기봉 순환",
        "area": "군포·안양",
        "latitude": 37.3675,
        "longitude": 126.9027,
        "distanceKm": 12.4,
        "ascentM": 780,
        "duration": "4시간~5시간",
        "difficulty": "중상",
        "surface": "암릉·계단·능선",
        "transport": "수리산역·명학역 방면",
        "bac": "블랙야크 100대 명산+",
        "summary": "암릉과 급경사를 섞어 기술적인 주행을 연습하기 좋은 코스",
        "caution": "비나 결빙 때 암릉 통과를 피하세요.",
        "heatExposure": 0.68,
        "wetSensitivity": 0.95,
    },
    {
        "id": "cheonggye-maebong",
        "name": "청계산 옛골·매봉 순환",
        "area": "성남·서울",
        "latitude": 37.4278,
        "longitude": 127.0435,
        "distanceKm": 11.7,
        "ascentM": 720,
        "duration": "3시간 30분~5시간",
        "difficulty": "중상",
        "surface": "계단·능선·흙길",
        "transport": "청계산입구역·옛골 방면",
        "bac": "블랙야크 100대 명산+",
        "summary": "교통이 편하고 계단·능선 강도를 함께 챙기기 좋은 코스",
        "caution": "주말 혼잡 시간에는 달리기보다 보행 전환 구간이 많아요.",
        "heatExposure": 0.64,
        "wetSensitivity": 0.72,
    },
    {
        "id": "gwanak-sadang",
        "name": "관악산 사당·연주대",
        "area": "서울·과천",
        "latitude": 37.4450,
        "longitude": 126.9640,
        "distanceKm": 12.8,
        "ascentM": 920,
        "duration": "4시간 30분~6시간",
        "difficulty": "상",
        "surface": "암릉·바위·급경사",
        "transport": "사당역 또는 과천향교 방면",
        "bac": "블랙야크 100대 명산",
        "summary": "바위와 급경사 대응 능력을 키우는 기술적인 산악 코스",
        "caution": "강풍·우천 때 노출 암릉은 위험하므로 추천에서 크게 감점해요.",
        "heatExposure": 0.88,
        "wetSensitivity": 1.0,
    },
    {
        "id": "samseong-hoam",
        "name": "삼성산·호암산 연계",
        "area": "서울·안양",
        "latitude": 37.4347,
        "longitude": 126.9282,
        "distanceKm": 14.1,
        "ascentM": 880,
        "duration": "4시간 30분~6시간",
        "difficulty": "중상",
        "surface": "바위·능선·숲길",
        "transport": "관악역·석수역 방면",
        "bac": "블랙야크 100대 명산 해당 없음",
        "summary": "관악산보다 한적한 바위 능선과 긴 연결 구간을 즐기는 코스",
        "caution": "바위 표면이 젖으면 속도를 크게 낮춰야 해요.",
        "heatExposure": 0.78,
        "wetSensitivity": 0.92,
    },
    {
        "id": "namhansanseong",
        "name": "남한산성 성곽·검단산 순환",
        "area": "광주·성남",
        "latitude": 37.4782,
        "longitude": 127.1810,
        "distanceKm": 15.6,
        "ascentM": 720,
        "duration": "4시간~5시간 30분",
        "difficulty": "중상",
        "surface": "성곽길·임도·숲길",
        "transport": "산성역·남한산성 로터리 방면",
        "bac": "블랙야크 100대 명산 해당 없음",
        "summary": "달릴 수 있는 완만한 구간이 비교적 많아 지속주 훈련에 적합",
        "caution": "성곽 주변 보행객이 많아 혼잡 시간에는 감속하세요.",
        "heatExposure": 0.58,
        "wetSensitivity": 0.55,
    },
    {
        "id": "bulgok-yeongjang",
        "name": "불곡산·영장산 연계",
        "area": "성남·분당",
        "latitude": 37.3699,
        "longitude": 127.1467,
        "distanceKm": 13.2,
        "ascentM": 610,
        "duration": "3시간 30분~5시간",
        "difficulty": "중",
        "surface": "흙길·완만한 능선",
        "transport": "오리역·태재고개 방면",
        "bac": "블랙야크 100대 명산 해당 없음",
        "summary": "완만한 흙길 비중이 높아 페이스 유지 훈련에 좋은 코스",
        "caution": "비 뒤 진흙이 오래 남는 구간이 있어 신발 선택이 중요해요.",
        "heatExposure": 0.52,
        "wetSensitivity": 0.78,
    },
    {
        "id": "seokseong-halmi",
        "name": "석성산·할미산성 순환",
        "area": "용인",
        "latitude": 37.2746,
        "longitude": 127.1777,
        "distanceKm": 10.8,
        "ascentM": 610,
        "duration": "3시간~4시간 30분",
        "difficulty": "중",
        "surface": "숲길·능선·계단",
        "transport": "동백·용인시청 방면",
        "bac": "블랙야크 100대 명산 해당 없음",
        "summary": "수원 동쪽에서 접근하기 좋고 숲길 비중이 높은 중거리 코스",
        "caution": "일부 도로 횡단과 갈림길에서 경로 확인이 필요해요.",
        "heatExposure": 0.48,
        "wetSensitivity": 0.65,
    },
    {
        "id": "wangsong-obong",
        "name": "왕송호수·오봉산 연계",
        "area": "의왕",
        "latitude": 37.3162,
        "longitude": 126.9496,
        "distanceKm": 12.1,
        "ascentM": 390,
        "duration": "2시간 30분~4시간",
        "difficulty": "중하",
        "surface": "호숫길·낮은 산길·임도",
        "transport": "의왕역·왕송호수 방면",
        "bac": "블랙야크 100대 명산 해당 없음",
        "summary": "날씨가 애매할 때 고산 코스 대신 선택하기 좋은 낮은 코스",
        "caution": "호숫가 노출 구간은 한여름 일사량과 맞바람 영향을 받아요.",
        "heatExposure": 0.7,
        "wetSensitivity": 0.42,
    },
]


def request_forecast(route: dict[str, Any]) -> dict[str, Any]:
    params = {
        "latitude": route["latitude"],
        "longitude": route["longitude"],
        "daily": ",".join(DAILY_FIELDS),
        "timezone": "Asia/Seoul",
        "forecast_days": 16,
    }
    url = f"{OPEN_METEO_URL}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "SuwonTrailWeeklyPlanner/1.0 (+https://github.com/lsh9955/test)"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        if response.status != 200:
            raise RuntimeError(f"Open-Meteo HTTP {response.status}")
        payload = json.load(response)
    daily = payload.get("daily")
    if not isinstance(daily, dict) or not daily.get("time"):
        raise RuntimeError(f"Open-Meteo daily data missing for {route['id']}")
    return daily


def value_at(daily: dict[str, Any], field: str, index: int, default: float | str = 0) -> Any:
    values = daily.get(field)
    if not isinstance(values, list) or index >= len(values) or values[index] is None:
        return default
    return values[index]


def next_weekend_indices(daily: dict[str, Any], now: datetime) -> list[int]:
    dates = [datetime.strptime(item, "%Y-%m-%d").date() for item in daily["time"]]
    today = now.date()
    days_until_saturday = (5 - today.weekday()) % 7
    if days_until_saturday == 0 and now.hour >= 18:
        days_until_saturday = 7
    saturday = today + timedelta(days=days_until_saturday)
    sunday = saturday + timedelta(days=1)
    wanted = {saturday, sunday}
    return [index for index, date in enumerate(dates) if date in wanted]


def weather_label(code: int) -> str:
    if code == 0:
        return "맑음"
    if code in (1, 2):
        return "대체로 맑음"
    if code == 3:
        return "흐림"
    if code in (45, 48):
        return "안개"
    if code in (51, 53, 55, 56, 57):
        return "이슬비"
    if code in (61, 63, 65, 66, 67, 80, 81, 82):
        return "비"
    if code in (71, 73, 75, 77, 85, 86):
        return "눈"
    if code in (95, 96, 99):
        return "뇌우"
    return "변동 가능"


def score_day(route: dict[str, Any], day: dict[str, Any]) -> tuple[int, list[str], str]:
    score = 100.0
    reasons: list[str] = []
    rain_prob = float(day["precipitationProbabilityPct"])
    rain_mm = float(day["precipitationMm"])
    wind = float(day["windKph"])
    gust = float(day["gustKph"])
    tmax = float(day["tempMaxC"])
    apparent = float(day["apparentMaxC"])
    uv = float(day["uvIndex"])
    code = int(day["weatherCode"])
    wet = float(route["wetSensitivity"])
    heat = float(route["heatExposure"])

    score -= min(36.0, rain_prob * 0.34)
    score -= min(24.0, rain_mm * 4.0) * wet
    if code in (95, 96, 99):
        score -= 42
        reasons.append("뇌우 가능성")
    elif code in (65, 67, 82, 86):
        score -= 24
        reasons.append("강한 강수 가능성")
    elif rain_prob >= 60 or rain_mm >= 5:
        reasons.append("비 가능성 높음")
    elif rain_prob <= 25 and rain_mm <= 1:
        score += 5
        reasons.append("강수 부담 적음")

    if wind > 18:
        score -= min(20, (wind - 18) * 1.2)
    if gust > 35:
        score -= min(22, (gust - 35) * 0.9)
        reasons.append("능선 돌풍 주의")
    elif wind <= 15:
        reasons.append("바람 무난")

    if apparent >= 33:
        score -= (apparent - 32) * 3.4 * heat
        reasons.append("체감 폭염")
    elif tmax >= 29:
        score -= (tmax - 28) * 2.1 * heat
        reasons.append("더위 대비 필요")
    elif 7 <= tmax <= 24:
        score += 4
        reasons.append("운동하기 좋은 기온")

    if uv >= 8:
        score -= 4 * heat
        reasons.append("자외선 매우 강함")
    elif uv >= 6:
        reasons.append("자외선 강함")

    if route["distanceKm"] >= 16 and (apparent >= 30 or rain_prob >= 50):
        score -= 10
        reasons.append("장거리 부담 증가")
    if route["wetSensitivity"] >= 0.9 and rain_mm >= 1:
        score -= 9
        reasons.append("젖은 암릉 위험")

    score = int(round(max(0, min(100, score))))
    if score >= 82:
        advice = "적극 추천"
    elif score >= 68:
        advice = "추천"
    elif score >= 52:
        advice = "조건부 추천"
    elif score >= 35:
        advice = "짧은 대체 코스 권장"
    else:
        advice = "산행 보류 권장"
    return score, reasons[:4], advice


def build_day(daily: dict[str, Any], index: int) -> dict[str, Any]:
    code = int(value_at(daily, "weather_code", index, 3))
    return {
        "date": value_at(daily, "time", index, ""),
        "weatherCode": code,
        "weatherLabel": weather_label(code),
        "tempMaxC": round(float(value_at(daily, "temperature_2m_max", index, 0)), 1),
        "tempMinC": round(float(value_at(daily, "temperature_2m_min", index, 0)), 1),
        "apparentMaxC": round(float(value_at(daily, "apparent_temperature_max", index, 0)), 1),
        "precipitationMm": round(float(value_at(daily, "precipitation_sum", index, 0)), 1),
        "precipitationProbabilityPct": int(round(float(value_at(daily, "precipitation_probability_max", index, 0)))),
        "windKph": round(float(value_at(daily, "wind_speed_10m_max", index, 0)), 1),
        "gustKph": round(float(value_at(daily, "wind_gusts_10m_max", index, 0)), 1),
        "uvIndex": round(float(value_at(daily, "uv_index_max", index, 0)), 1),
        "sunrise": str(value_at(daily, "sunrise", index, ""))[-5:],
        "sunset": str(value_at(daily, "sunset", index, ""))[-5:],
    }


def compact_route(route: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in route.items() if key not in {"latitude", "longitude", "heatExposure", "wetSensitivity"}}


def generate() -> dict[str, Any]:
    now = datetime.now(KST)
    evaluated: list[dict[str, Any]] = []
    weekend_dates: list[str] = []

    for index, route in enumerate(ROUTES):
        daily = request_forecast(route)
        weekend_indices = next_weekend_indices(daily, now)
        if len(weekend_indices) != 2:
            raise RuntimeError(f"Weekend forecast missing for {route['id']}")
        days: list[dict[str, Any]] = []
        for day_index in weekend_indices:
            day = build_day(daily, day_index)
            score, reasons, advice = score_day(route, day)
            day.update({"score": score, "reasons": reasons, "advice": advice})
            days.append(day)
        if not weekend_dates:
            weekend_dates = [day["date"] for day in days]
        best = max(days, key=lambda item: item["score"])
        route_result = compact_route(route)
        route_result.update(
            {
                "bestDay": best["date"],
                "bestScore": best["score"],
                "bestAdvice": best["advice"],
                "bestReasons": best["reasons"],
                "weather": days,
            }
        )
        evaluated.append(route_result)
        if index + 1 < len(ROUTES):
            time.sleep(0.15)

    evaluated.sort(key=lambda item: (-item["bestScore"], item["distanceKm"]))
    recommendations = []
    for rank, item in enumerate(evaluated[:5], start=1):
        recommendation = dict(item)
        recommendation["rank"] = rank
        recommendations.append(recommendation)

    warnings: list[str] = []
    top_weather = [day for item in evaluated[:3] for day in item["weather"]]
    if any(day["precipitationProbabilityPct"] >= 70 for day in top_weather):
        warnings.append("추천 상위 코스에도 비 가능성이 있어 출발 직전 레이더와 통제 정보를 다시 확인하세요.")
    if any(day["apparentMaxC"] >= 33 for day in top_weather):
        warnings.append("체감온도가 높아 오전 이른 출발, 충분한 물과 전해질 준비가 필요해요.")
    if any(day["gustKph"] >= 40 for day in top_weather):
        warnings.append("능선 돌풍 가능성이 있어 암릉·노출 구간 코스는 피하는 편이 좋아요.")
    warnings.append("산악 날씨는 지형에 따라 달라질 수 있으며, 입산 통제·산불·낙뢰 특보는 출발 직전에 별도 확인하세요.")

    return {
        "schemaVersion": 1,
        "generatedAt": now.isoformat(timespec="seconds"),
        "refreshSchedule": "매주 월요일 05:40 KST 자동 갱신",
        "source": {
            "name": "Open-Meteo Forecast API",
            "url": "https://open-meteo.com/en/docs",
            "note": "공개 예보와 고정 코스 메타데이터만 사용하며 개인 운동 데이터는 사용하지 않아요.",
        },
        "weekend": {
            "saturday": weekend_dates[0],
            "sunday": weekend_dates[1],
        },
        "recommendations": recommendations,
        "routes": evaluated,
        "warnings": warnings,
    }


def validate(snapshot: dict[str, Any]) -> None:
    if snapshot.get("schemaVersion") != 1:
        raise RuntimeError("schemaVersion must be 1")
    recommendations = snapshot.get("recommendations")
    if not isinstance(recommendations, list) or len(recommendations) < 3:
        raise RuntimeError("at least three recommendations are required")
    for item in recommendations:
        if not item.get("name") or not isinstance(item.get("weather"), list):
            raise RuntimeError("invalid recommendation item")
        score = item.get("bestScore")
        if not isinstance(score, int) or not 0 <= score <= 100:
            raise RuntimeError("score outside 0..100")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="suwon-trail/weekly.json")
    args = parser.parse_args()
    snapshot = generate()
    validate(snapshot)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {output} with {len(snapshot['routes'])} routes")


if __name__ == "__main__":
    main()
