from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

import requests


@dataclass(frozen=True)
class WeatherReport:
    city: str
    weather_desc: str
    temp_c: int | None
    feels_like_c: int | None
    humidity: int | None
    wind_kmph: int | None
    precip_mm: float | None
    uv_index: int | None
    raw: dict[str, Any]

    def summary(self) -> str:
        temp = "未知" if self.temp_c is None else f"{self.temp_c}摄氏度"
        return f"{self.city}当前天气:{self.weather_desc}，气温{temp}"


def _to_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _to_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def get_weather(city: str, *, lang: str = "zh", timeout: float = 10.0) -> WeatherReport:
    """
    通过调用 wttr.in API 查询真实的天气信息。
    """
    safe_city = quote(city.strip())
    url = f"https://wttr.in/{safe_city}?format=j1&lang={quote(lang)}"

    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        data = response.json()

        current_condition = data["current_condition"][0]
        weather_desc = current_condition["weatherDesc"][0]["value"]

        return WeatherReport(
            city=city,
            weather_desc=weather_desc,
            temp_c=_to_int(current_condition.get("temp_C")),
            feels_like_c=_to_int(current_condition.get("FeelsLikeC")),
            humidity=_to_int(current_condition.get("humidity")),
            wind_kmph=_to_int(current_condition.get("windspeedKmph")),
            precip_mm=_to_float(current_condition.get("precipMM")),
            uv_index=_to_int(current_condition.get("uvIndex")),
            raw=data,
        )
    except requests.exceptions.RequestException as exc:
        raise RuntimeError(f"查询天气时遇到网络问题 - {exc}") from exc
    except (KeyError, IndexError, ValueError) as exc:
        raise RuntimeError(f"解析天气数据失败，可能是城市名称无效 - {exc}") from exc


def get_weather_text(city: str) -> str:
    """
    兼容用户提供的工具形式：返回一句自然语言天气描述。
    """
    try:
        return get_weather(city).summary()
    except RuntimeError as exc:
        return f"错误:{exc}"
