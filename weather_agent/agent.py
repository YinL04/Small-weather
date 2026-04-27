from __future__ import annotations

from dataclasses import dataclass

from .config import Settings
from .tools import WeatherReport, get_weather


RAIN_KEYWORDS = ("雨", "drizzle", "rain", "shower", "storm", "thunder")
SNOW_KEYWORDS = ("雪", "snow", "sleet", "blizzard")
CLOUD_KEYWORDS = ("云", "阴", "cloud", "overcast")
SUN_KEYWORDS = ("晴", "sun", "clear")


@dataclass(frozen=True)
class AgentAnswer:
    city: str
    text: str
    used_llm: bool


class WeatherAgent:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = self._build_client()

    def run(self, city: str) -> AgentAnswer:
        city = city.strip()
        if not city:
            raise ValueError("城市名称不能为空")

        report = get_weather(
            city,
            lang=self.settings.wttr_lang,
            timeout=self.settings.wttr_timeout,
        )

        if self.client:
            llm_text = self._generate_with_llm(report)
            if llm_text:
                return AgentAnswer(city=city, text=llm_text, used_llm=True)

        return AgentAnswer(city=city, text=self._generate_rule_based(report), used_llm=False)

    def _build_client(self):
        if not self.settings.llm_enabled:
            return None

        try:
            from openai import OpenAI
        except ImportError:
            return None

        return OpenAI(
            api_key=self.settings.openai_api_key,
            base_url=self.settings.openai_base_url,
        )

    def _generate_with_llm(self, report: WeatherReport) -> str:
        prompt = f"""
你是一个中文天气出行 agent。请基于真实天气信息，给用户简洁、实用的当天出行建议，并推荐这个城市适合游览的景点。

城市：{report.city}
天气：{report.weather_desc}
气温：{report.temp_c}
体感温度：{report.feels_like_c}
湿度：{report.humidity}
风速 km/h：{report.wind_kmph}
降水 mm：{report.precip_mm}
紫外线指数：{report.uv_index}

输出要求：
1. 先用一句话说明当前天气。
2. 给出 3 条当天出行建议。
3. 推荐 3-5 个该城市旅游景点，并说明为什么适合或需要注意什么。
4. 不要编造具体门票价格、开放时间或临时活动。
""".strip()

        try:
            response = self.client.chat.completions.create(
                model=self.settings.openai_model,
                messages=[
                    {"role": "system", "content": "你是可靠、克制、实用的中文旅行天气助手。"},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.4,
            )
            return response.choices[0].message.content or ""
        except Exception as exc:
            return (
                f"{self._generate_rule_based(report)}\n\n"
                f"提示：大模型建议生成失败，已使用内置规则。错误信息：{exc}"
            )

    def _generate_rule_based(self, report: WeatherReport) -> str:
        advice = self._travel_advice(report)
        attractions = self._attractions(report)

        lines = [
            report.summary(),
            "",
            "出行建议：",
            *[f"- {item}" for item in advice],
            "",
            "景点推荐：",
            *[f"- {item}" for item in attractions],
        ]
        return "\n".join(lines)

    def _travel_advice(self, report: WeatherReport) -> list[str]:
        desc = report.weather_desc.lower()
        advice: list[str] = []

        if any(word in desc for word in RAIN_KEYWORDS) or (report.precip_mm or 0) > 0:
            advice.append("带伞或轻便雨衣，优先安排博物馆、展馆、商圈等室内路线。")
        elif any(word in desc for word in SNOW_KEYWORDS):
            advice.append("注意保暖和防滑，鞋子选择抓地力好的款式，预留更多交通时间。")
        elif any(word in desc for word in SUN_KEYWORDS):
            advice.append("适合户外步行和城市观景，午后注意补水。")
        elif any(word in desc for word in CLOUD_KEYWORDS):
            advice.append("云量较多，适合长时间步行游览，拍照光线通常更柔和。")
        else:
            advice.append("适合正常出行，建议出门前再确认一次短时天气变化。")

        if report.temp_c is not None:
            if report.temp_c >= 30:
                advice.append("气温偏高，避开正午暴晒时段，安排早晚户外活动更舒服。")
            elif report.temp_c <= 5:
                advice.append("气温较低，穿厚外套，减少长时间户外等待。")
            else:
                advice.append("气温相对舒适，可以安排半日到一日的城市漫游。")

        if report.uv_index is not None and report.uv_index >= 6:
            advice.append("紫外线较强，准备防晒霜、帽子或太阳镜。")
        elif report.wind_kmph is not None and report.wind_kmph >= 30:
            advice.append("风力偏大，少带容易被风吹动的物品，登高观景注意安全。")

        return advice[:3]

    def _attractions(self, report: WeatherReport) -> list[str]:
        desc = report.weather_desc.lower()
        rainy = any(word in desc for word in RAIN_KEYWORDS) or (report.precip_mm or 0) > 0
        very_hot = report.temp_c is not None and report.temp_c >= 30
        very_cold = report.temp_c is not None and report.temp_c <= 5

        if rainy or very_hot or very_cold:
            return [
                f"{report.city}博物馆或城市展览馆：室内为主，受天气影响小。",
                f"{report.city}历史街区：选择有商铺、咖啡馆和室内休息点的路线。",
                f"{report.city}大型商圈或美食街：适合把餐饮、购物和短途散步放在一起。",
                f"{report.city}地标建筑观景区：天气间隙前往，注意能见度和排队时间。",
            ]

        return [
            f"{report.city}城市公园：适合散步、拍照和感受当地生活节奏。",
            f"{report.city}历史文化街区：适合步行游览，顺路体验小吃和本地店铺。",
            f"{report.city}代表性地标：适合作为当天主线行程，安排在光线好的时段。",
            f"{report.city}河岸、湖边或山景步道：天气稳定时适合慢行和观景。",
            f"{report.city}夜景观赏点：如果傍晚天气仍好，可以作为收尾行程。",
        ]
