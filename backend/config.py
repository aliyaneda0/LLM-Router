from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    local_weak_model: str = os.getenv("LOCAL_WEAK_MODEL", "llama3.2:1b")
    local_moderate_model: str = os.getenv("LOCAL_MODERATE_MODEL", "phi3.5")
    strong_api_model: str = os.getenv("STRONG_API_MODEL", "gpt-4o-mini")
    confidence_fallback_threshold: float = float(
        os.getenv("CONFIDENCE_FALLBACK_THRESHOLD", "0.55")
    )
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")


def get_settings() -> Settings:
    return Settings()
