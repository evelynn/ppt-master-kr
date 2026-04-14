#!/usr/bin/env python3
"""PPT Master - Internationalization (i18n) Module.

Loads language settings and translation strings for all user-facing output.

Usage:
    from i18n import t, get_language, set_language

    print(t("project.created", path=project_path))
    lang = get_language()           # -> 'ko' | 'en' | 'auto'
    set_language('ko')              # persist to settings.json

Language resolution order (highest priority first):
    1. PPT_MASTER_LANG environment variable (if set to a valid code)
    2. `language` field in <skill_root>/settings.json
    3. LANG / LC_ALL environment variable prefix match (ko_KR -> 'ko')
    4. Default: 'en'
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
SETTINGS_FILE = SKILL_DIR / "settings.json"
I18N_DIR = SKILL_DIR / "i18n"

SUPPORTED_LANGUAGES = ("en", "ko")
DEFAULT_LANGUAGE = "en"

_cache: Dict[str, Dict[str, Any]] = {}
_cached_lang: Optional[str] = None


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def load_settings() -> Dict[str, Any]:
    """Load settings.json (returns empty dict if missing)."""
    return _load_json(SETTINGS_FILE)


def save_settings(settings: Dict[str, Any]) -> None:
    """Persist settings.json."""
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with SETTINGS_FILE.open("w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)
        f.write("\n")


def _detect_system_language() -> str:
    """Derive language from LANG / LC_ALL env vars."""
    for env_var in ("LC_ALL", "LC_MESSAGES", "LANG"):
        value = os.environ.get(env_var)
        if not value:
            continue
        code = value.split(".", 1)[0].split("_", 1)[0].lower()
        if code in SUPPORTED_LANGUAGES:
            return code
    return DEFAULT_LANGUAGE


def get_language() -> str:
    """Resolve the active language code.

    Returns one of SUPPORTED_LANGUAGES (never 'auto').
    """
    global _cached_lang
    if _cached_lang is not None:
        return _cached_lang

    # 1. Environment override
    env_lang = os.environ.get("PPT_MASTER_LANG", "").strip().lower()
    if env_lang in SUPPORTED_LANGUAGES:
        _cached_lang = env_lang
        return env_lang

    # 2. settings.json
    settings = load_settings()
    lang = str(settings.get("language", "auto")).strip().lower()
    if lang in SUPPORTED_LANGUAGES:
        _cached_lang = lang
        return lang

    # 3. system locale (auto / unknown)
    _cached_lang = _detect_system_language()
    return _cached_lang


def set_language(lang: str) -> str:
    """Persist a language preference to settings.json.

    Accepts 'en', 'ko', or 'auto'. Returns the value that was written.
    """
    global _cached_lang
    lang_norm = lang.strip().lower()
    if lang_norm not in SUPPORTED_LANGUAGES and lang_norm != "auto":
        raise ValueError(
            f"Unsupported language: {lang!r}. "
            f"Supported: {', '.join(SUPPORTED_LANGUAGES)}, auto"
        )
    settings = load_settings()
    settings["language"] = lang_norm
    save_settings(settings)
    _cached_lang = None  # invalidate cache so next get_language() re-resolves
    return lang_norm


def _load_messages(lang: str) -> Dict[str, Any]:
    if lang in _cache:
        return _cache[lang]
    path = I18N_DIR / f"{lang}.json"
    messages = _load_json(path)
    _cache[lang] = messages
    return messages


def _resolve_key(messages: Dict[str, Any], key: str) -> Optional[str]:
    """Resolve dotted key path (e.g. 'project.created')."""
    node: Any = messages
    for part in key.split("."):
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node if isinstance(node, str) else None


def t(key: str, **kwargs: Any) -> str:
    """Translate a dotted key to the active language.

    Falls back to English, then to the key itself if no translation found.
    Supports str.format() keyword interpolation.
    """
    lang = get_language()
    value = _resolve_key(_load_messages(lang), key)
    if value is None and lang != DEFAULT_LANGUAGE:
        value = _resolve_key(_load_messages(DEFAULT_LANGUAGE), key)
    if value is None:
        value = key
    if kwargs:
        try:
            return value.format(**kwargs)
        except (KeyError, IndexError):
            return value
    return value


def reset_cache() -> None:
    """Clear in-memory caches (useful in tests)."""
    global _cached_lang
    _cached_lang = None
    _cache.clear()


def main() -> None:
    """CLI entry: `python3 i18n.py [key]` — prints translation."""
    import sys

    if len(sys.argv) < 2:
        print(f"Active language: {get_language()}")
        print(f"Settings file:   {SETTINGS_FILE}")
        print(f"Supported:       {', '.join(SUPPORTED_LANGUAGES)}, auto")
        return
    key = sys.argv[1]
    print(t(key))


if __name__ == "__main__":
    main()
