from __future__ import annotations

import copy
import os
from pathlib import Path
from threading import RLock
from typing import Any

import yaml


CONFIG_PATH = Path(os.getenv("CONFIG_PATH", Path(__file__).with_name("config.yaml")))

_DEFAULT_CONFIG: dict[str, Any] = {
    "ai": {
        "mode": "hybrid",
        "cloud_enabled": True,
        "local_enabled": True,
        "cloud_model": "gpt-4o-mini",
        "local_model": "tinyllama",
        "local_url": "http://ollama:11434/api/generate",
    },
    "stt": {
        "engine": "whisper",
        "model": "small",
    },
    "tts": {
        "engine": "piper",
        "model": "ru_RU-irina-medium.onnx",
    },
    "features": {
        "cloud_ai": True,
        "local_fallback": True,
        "local_only_mode": False,
        "skills_engine": True,
        "conversation_memory": False,
        "wake_word": False,
        "piper_tts": True,
        "web_tts": False,
        "debug_logging": False,
        "skills": True,
        "memory": False,
        "enabled_skills": ["help"],
    },
    "roadmap": [
        {"component": "Whisper STT", "status": "implemented"},
        {"component": "Skill Engine", "status": "in_progress"},
        {"component": "Wake Word", "status": "planned"},
        {"component": "Memory", "status": "experimental"},
        {"component": "Web Client", "status": "implemented"},
    ],
}

_lock = RLock()


def _deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    merged = copy.deepcopy(base)
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
            continue
        merged[key] = value
    return merged


def ensure_config_file() -> None:
    with _lock:
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        if not CONFIG_PATH.exists():
            with CONFIG_PATH.open("w", encoding="utf-8") as handle:
                yaml.safe_dump(
                    _DEFAULT_CONFIG,
                    handle,
                    sort_keys=False,
                    allow_unicode=True,
                )


def load_config() -> dict[str, Any]:
    ensure_config_file()
    with _lock:
        with CONFIG_PATH.open("r", encoding="utf-8") as handle:
            loaded = yaml.safe_load(handle) or {}
        if not isinstance(loaded, dict):
            loaded = {}
        return _deep_merge(_DEFAULT_CONFIG, loaded)


def save_config(data: dict[str, Any]) -> dict[str, Any]:
    merged = _deep_merge(_DEFAULT_CONFIG, data)
    with _lock:
        with CONFIG_PATH.open("w", encoding="utf-8") as handle:
            yaml.safe_dump(
                merged,
                handle,
                sort_keys=False,
                allow_unicode=True,
            )
    return merged


def update_config(patch: dict[str, Any]) -> dict[str, Any]:
    current = load_config()
    updated = _deep_merge(current, patch)
    return save_config(updated)


def set_feature(feature: str, enabled: bool) -> dict[str, Any]:
    current = load_config()
    current.setdefault("features", {})
    current["features"][feature] = enabled

    if feature == "cloud_ai":
        current.setdefault("ai", {})["cloud_enabled"] = enabled
    elif feature == "local_fallback":
        current.setdefault("ai", {})["local_enabled"] = enabled
    elif feature == "local_only_mode":
        current.setdefault("ai", {})["mode"] = "local" if enabled else "hybrid"
    elif feature == "skills_engine":
        current.setdefault("features", {})["skills"] = enabled
    elif feature == "conversation_memory":
        current.setdefault("features", {})["memory"] = enabled
    elif feature == "piper_tts" and enabled:
        current.setdefault("tts", {})["engine"] = "piper"
    elif feature == "web_tts" and enabled:
        current.setdefault("tts", {})["engine"] = "web"

    return save_config(current)
