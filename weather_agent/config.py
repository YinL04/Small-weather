from dataclasses import dataclass
import os

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    openai_api_key: str
    openai_base_url: str
    openai_model: str
    wttr_lang: str
    wttr_timeout: float
    default_city: str

    @property
    def llm_enabled(self) -> bool:
        return bool(self.openai_api_key.strip())


def load_settings() -> Settings:
    load_dotenv()

    timeout_raw = os.getenv("WTTR_TIMEOUT", "10")
    try:
        wttr_timeout = float(timeout_raw)
    except ValueError:
        wttr_timeout = 10.0

    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openai_base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        wttr_lang=os.getenv("WTTR_LANG", "zh"),
        wttr_timeout=wttr_timeout,
        default_city=os.getenv("DEFAULT_CITY", ""),
    )
