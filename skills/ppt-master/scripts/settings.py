#!/usr/bin/env python3
"""PPT Master - Settings CLI.

Read and write the global PPT Master settings file (skills/ppt-master/settings.json).
Primary use case: switching the user-interface and AI response language.

Usage:
    # Show current settings
    python3 scripts/settings.py show

    # Set language to Korean  (한국어로 전환)
    python3 scripts/settings.py set-language ko

    # Set language to English
    python3 scripts/settings.py set-language en

    # Follow system locale (LANG / LC_ALL)
    python3 scripts/settings.py set-language auto

    # Get the resolved active language
    python3 scripts/settings.py get-language

When the language is set to "ko", every PPT Master tool prints Korean, the
`SKILL.md` workflow directs the AI to respond in Korean, and all feature
descriptions / prompts are served from the Korean resource bundle.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from i18n import (  # noqa: E402
    SETTINGS_FILE,
    SUPPORTED_LANGUAGES,
    get_language,
    load_settings,
    reset_cache,
    set_language,
    t,
)

LANGUAGE_CHOICES = tuple(list(SUPPORTED_LANGUAGES) + ["auto"])


def cmd_show(_args: argparse.Namespace) -> int:
    settings = load_settings()
    stored = settings.get("language", "auto")
    active = get_language()
    print(t("settings.header"))
    print("-" * 40)
    print(t("settings.file", path=str(SETTINGS_FILE)))
    print(t("settings.stored_language", value=stored))
    print(t("settings.active_language", value=active))
    if settings:
        other = {k: v for k, v in settings.items() if k != "language"}
        if other:
            print()
            print(t("settings.other_keys"))
            print(json.dumps(other, ensure_ascii=False, indent=2))
    return 0


def cmd_set_language(args: argparse.Namespace) -> int:
    try:
        written = set_language(args.language)
    except ValueError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2
    reset_cache()
    active = get_language()
    # Print confirmation in the NEW language
    print(t("settings.language_updated", value=written))
    print(t("settings.active_language", value=active))
    if written == "ko":
        print()
        print("안내: 이제부터 PPT Master의 모든 명령어 출력과 AI 응답은 한국어로 제공됩니다.")
    elif written == "en":
        print()
        print("Note: All PPT Master command output and AI responses will now be in English.")
    return 0


def cmd_get_language(_args: argparse.Namespace) -> int:
    print(get_language())
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="settings.py",
        description="Manage PPT Master global settings (language, etc).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("show", help="Show current settings")

    sl = sub.add_parser("set-language", help="Set active language")
    sl.add_argument(
        "language",
        choices=LANGUAGE_CHOICES,
        help="Language code: 'en', 'ko', or 'auto' (follow system locale)",
    )

    sub.add_parser("get-language", help="Print the currently resolved language")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    dispatch = {
        "show": cmd_show,
        "set-language": cmd_set_language,
        "get-language": cmd_get_language,
    }
    return dispatch[args.command](args)


if __name__ == "__main__":
    raise SystemExit(main())
