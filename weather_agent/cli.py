import argparse

from .agent import WeatherAgent
from .config import load_settings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="查询城市天气并生成出行建议。")
    parser.add_argument("city", nargs="?", help="要查询的城市，例如：北京、Shanghai、London")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = load_settings()
    city = args.city or settings.default_city

    if not city:
        city = input("请输入想查询天气的城市：").strip()

    agent = WeatherAgent(settings)

    try:
        answer = agent.run(city)
    except Exception as exc:
        print(f"错误:{exc}")
        return

    print(answer.text)
    if not answer.used_llm:
        print("\n提示：当前未配置 OPENAI_API_KEY，已使用内置规则生成建议。")


if __name__ == "__main__":
    main()
