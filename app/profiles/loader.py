from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

_PROFILES_PATH = Path(__file__).parent / "profiles.yaml"


@dataclass
class Profile:
    system_prompt: str
    temperature: float | None = None
    max_tokens: int | None = None
    model: str | None = None
    base_url: str | None = None


@lru_cache(maxsize=1)
def load_profiles() -> dict[str, Profile]:
    raw = yaml.safe_load(_PROFILES_PATH.read_text(encoding="utf-8"))
    return {name: Profile(**data) for name, data in raw.items()}


def get_profile(name: str) -> Profile:
    profiles = load_profiles()
    return profiles.get(name) or profiles["default"]
