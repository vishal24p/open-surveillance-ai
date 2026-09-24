from dataclasses import dataclass
from math import isfinite
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Settings:
    droidcam_index: int
    person_confidence: float


def load_settings(env_path: Path = Path(".env")) -> Settings:
    return Settings(
        droidcam_index=get_droidcam_index(env_path),
        person_confidence=get_person_confidence(env_path),
    )


def get_droidcam_index(env_path: Path = Path(".env")) -> int:
    value = _read_env_value(env_path, "DROIDCAM_INDEX")

    if value is None:
        raise RuntimeError("Set DROIDCAM_INDEX in .env.")

    try:
        index = int(value)
    except ValueError as error:
        raise RuntimeError("DROIDCAM_INDEX must be a non-negative integer.") from error

    if index < 0:
        raise RuntimeError("DROIDCAM_INDEX must be a non-negative integer.")

    return index


def get_person_confidence(env_path: Path = Path(".env")) -> float:
    value = _read_env_value(env_path, "PERSON_CONFIDENCE")
    if value is None:
        raise RuntimeError(
            "PERSON_CONFIDENCE is missing in .env; no fallback is configured."
        )

    try:
        confidence = float(value)
    except ValueError as error:
        raise RuntimeError("PERSON_CONFIDENCE must be a number from 0 to 1.") from error

    if not isfinite(confidence) or not 0 <= confidence <= 1:
        raise RuntimeError("PERSON_CONFIDENCE must be a number from 0 to 1.")

    return confidence


def _read_env_value(env_path: Path, key_name: str) -> str | None:
    if not env_path.is_file():
        raise RuntimeError("Create .env from .env.example before running the camera.")

    for line in env_path.read_text(encoding="utf-8").splitlines():
        key, separator, value = line.partition("=")
        if separator and key.strip() == key_name:
            return value.strip().strip('"').strip("'")

    return None
