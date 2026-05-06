#!/usr/bin/env python3
"""
PPT Master - outline.yaml manager.

Manages the project-level slide outline that drives the editor UI and the
4-unit regeneration pipeline (slide / section / theme / reorganize).

outline.yaml schema (informal):

    meta:
      canvas: ppt169
      template: minimax_demo
      design_system: DESIGN.md     # path relative to template dir
      total_slides: <int>          # auto-computed
      created: <iso-date>
      updated: <iso-date>
    theme_overrides:
      colors:
        brand-1: "#FF5500"
      typography:
        heading-lg: { size_px: 52 }
    sections:
      - id: intro
        title: 도입
        slides: [01_cover, 02_toc]
      - id: products
        title: 제품군
        slides: [03_m27, 04_music]
    slides:
      - id: 03_m27
        section: products
        slide_template: product_showcase_2up
        title: M2.7 Foundation Model
        subtitle: 차세대 한국어 추론 모델
        components:
          - "product-cards/coral?title=M2.7&subtitle=Foundation Model&x=80&y=120&w=480&h=400"
        bullets:
          - 200B 파라미터
          - 한국어 평균 +18%
        notes: ...
        last_changed: <iso-date>     # touched whenever the slide is edited
        last_finalized: <iso-date>   # touched whenever the slide passes finalize_svg
        dirty: true|false            # true ⇒ needs regeneration

CLI:
    python3 outline_manager.py generate <project> [--from-design-spec]
    python3 outline_manager.py validate <project>
    python3 outline_manager.py diff <old.yaml> <new.yaml>
    python3 outline_manager.py renumber <project> [--start 1]
    python3 outline_manager.py touch <project> --slides 03_m27,04_music
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

SCHEMA_VERSION = 1
SLIDE_ID_RE = re.compile(r"^\d{2,3}_[a-z0-9_]+$")


# ---------------------------------------------------------------------------
# Loading and saving
# ---------------------------------------------------------------------------

def _outline_path(project_dir: Path) -> Path:
    return Path(project_dir) / "outline.yaml"


def load(project_dir: Path) -> dict:
    p = _outline_path(project_dir)
    if not p.exists():
        return {}
    with p.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def save(project_dir: Path, outline: dict) -> Path:
    p = _outline_path(project_dir)
    outline.setdefault("meta", {})["updated"] = datetime.date.today().isoformat()
    outline["meta"]["schema"] = SCHEMA_VERSION
    outline["meta"]["total_slides"] = len(outline.get("slides", []))
    with p.open("w", encoding="utf-8") as f:
        yaml.safe_dump(outline, f, sort_keys=False, allow_unicode=True, default_flow_style=False)
    return p


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def generate(project_dir: Path, *, from_design_spec: bool = False) -> dict:
    """Build a starter outline.yaml from the project's existing SVGs."""
    pd = Path(project_dir)
    svg_dir = pd / "svg_output"
    if not svg_dir.exists():
        svg_dir = pd / "svg_final"
    svg_files = sorted(svg_dir.glob("*.svg")) if svg_dir.exists() else []

    template = ""
    pointer = pd / ".ppt-master" / "template.txt"
    if pointer.exists():
        template = pointer.read_text(encoding="utf-8").strip()

    outline = {
        "meta": {
            "schema": SCHEMA_VERSION,
            "canvas": "ppt169",
            "template": template,
            "design_system": "DESIGN.md",
            "total_slides": len(svg_files),
            "created": datetime.date.today().isoformat(),
            "updated": datetime.date.today().isoformat(),
        },
        "theme_overrides": {},
        "sections": [
            {"id": "all", "title": "All slides",
             "slides": [f.stem for f in svg_files]},
        ],
        "slides": [
            {
                "id": f.stem,
                "section": "all",
                "slide_template": _guess_slide_template(f.stem),
                "title": _humanize(f.stem),
                "subtitle": "",
                "components": [],
                "bullets": [],
                "notes": "",
                "dirty": False,
            }
            for f in svg_files
        ],
    }

    if from_design_spec:
        spec_path = pd / "design_spec.md"
        if spec_path.exists():
            _enrich_from_design_spec(outline, spec_path)

    return outline


def _humanize(slide_id: str) -> str:
    parts = slide_id.split("_", 1)
    return parts[1].replace("_", " ").title() if len(parts) > 1 else slide_id


def _guess_slide_template(slide_id: str) -> str:
    name = slide_id.split("_", 1)[-1].lower()
    if "cover" in name:
        return "cover_dark"
    if "toc" in name or "outline" in name:
        return "content_steps_3"
    if "chapter" in name or "section" in name:
        return "section_divider"
    if "ending" in name or "thanks" in name:
        return "ending_thanks"
    return "content_default"


def _enrich_from_design_spec(outline: dict, spec_path: Path) -> None:
    """Walk a design_spec.md and copy slide titles into matching outline slides."""
    text = spec_path.read_text(encoding="utf-8")
    by_id = {s["id"]: s for s in outline["slides"]}
    for m in re.finditer(r"#### Slide\s+(\d+)\s*[—-]\s*([^\n]+)", text):
        num = int(m.group(1))
        title = m.group(2).strip()
        for sid, slide in by_id.items():
            if sid.startswith(f"{num:02d}_"):
                if not slide.get("title"):
                    slide["title"] = title
                break


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate(project_dir: Path) -> list[str]:
    errors: list[str] = []
    outline = load(project_dir)
    if not outline:
        return [f"outline.yaml not found in {project_dir}"]

    meta = outline.get("meta", {})
    if "canvas" not in meta:
        errors.append("meta.canvas missing")
    if "template" not in meta:
        errors.append("meta.template missing")

    section_ids = {s.get("id") for s in outline.get("sections", [])}
    if not section_ids:
        errors.append("No sections defined")

    slide_ids: set[str] = set()
    for slide in outline.get("slides", []):
        sid = slide.get("id", "")
        if not SLIDE_ID_RE.match(sid):
            errors.append(f"Invalid slide id format: {sid!r}")
        if sid in slide_ids:
            errors.append(f"Duplicate slide id: {sid!r}")
        slide_ids.add(sid)
        if slide.get("section") and slide["section"] not in section_ids:
            errors.append(f"Slide {sid!r} references unknown section {slide['section']!r}")

    # Cross-check sections.slides ⊆ slides.id
    for s in outline.get("sections", []):
        for sid in s.get("slides", []):
            if sid not in slide_ids:
                errors.append(f"Section {s.get('id')!r} lists missing slide {sid!r}")

    return errors


# ---------------------------------------------------------------------------
# Diff
# ---------------------------------------------------------------------------

def diff(old: dict, new: dict) -> dict:
    """Return a minimal change description between two outlines."""
    old_slides = {s["id"]: s for s in old.get("slides", [])}
    new_slides = {s["id"]: s for s in new.get("slides", [])}

    added = [sid for sid in new_slides if sid not in old_slides]
    removed = [sid for sid in old_slides if sid not in new_slides]
    changed = []
    for sid in new_slides:
        if sid in old_slides and _slide_signature(old_slides[sid]) != _slide_signature(new_slides[sid]):
            changed.append(sid)

    theme_changed = (
        old.get("theme_overrides", {}) != new.get("theme_overrides", {})
    )
    order_changed = (
        [s["id"] for s in old.get("slides", [])]
        != [s["id"] for s in new.get("slides", [])]
    )
    sections_changed = old.get("sections") != new.get("sections")

    return {
        "added": added,
        "removed": removed,
        "changed": changed,
        "theme_changed": theme_changed,
        "order_changed": order_changed,
        "sections_changed": sections_changed,
    }


def _slide_signature(slide: dict) -> tuple:
    """A tuple of fields whose change implies the slide must be re-rendered."""
    return (
        slide.get("title", ""),
        slide.get("subtitle", ""),
        slide.get("slide_template", ""),
        tuple(slide.get("components", [])),
        tuple(slide.get("bullets", [])),
        slide.get("notes", ""),
    )


# ---------------------------------------------------------------------------
# Renumbering
# ---------------------------------------------------------------------------

def renumber(project_dir: Path, start: int = 1) -> dict[str, str]:
    """Renumber slides 01_, 02_, ... in current order. Returns old→new id map."""
    pd = Path(project_dir)
    outline = load(pd)
    if not outline:
        return {}
    rename: dict[str, str] = {}

    width = max(2, len(str(start + len(outline.get("slides", [])) - 1)))
    for i, slide in enumerate(outline["slides"]):
        old_id = slide["id"]
        suffix = old_id.split("_", 1)[1] if "_" in old_id else old_id
        new_id = f"{start + i:0{width}d}_{suffix}"
        if new_id != old_id:
            rename[old_id] = new_id
            slide["id"] = new_id

    if not rename:
        return {}

    # Rewrite section.slides
    for s in outline.get("sections", []):
        s["slides"] = [rename.get(x, x) for x in s.get("slides", [])]

    # Rename SVG files in svg_output (and svg_final if present, and notes/)
    for sub in ("svg_output", "svg_final", "notes"):
        d = pd / sub
        if not d.exists():
            continue
        for old_id, new_id in rename.items():
            for src in d.glob(f"{old_id}*"):
                dst = src.with_name(src.name.replace(old_id, new_id, 1))
                src.rename(dst)

    save(pd, outline)
    return rename


# ---------------------------------------------------------------------------
# Touch
# ---------------------------------------------------------------------------

def touch(project_dir: Path, slide_ids: list[str]) -> int:
    outline = load(project_dir)
    if not outline:
        return 0
    today = datetime.date.today().isoformat()
    n = 0
    for slide in outline.get("slides", []):
        if slide["id"] in slide_ids:
            slide["last_changed"] = today
            slide["dirty"] = True
            n += 1
    save(project_dir, outline)
    return n


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _cli() -> int:
    p = argparse.ArgumentParser(description="outline.yaml manager")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_gen = sub.add_parser("generate")
    p_gen.add_argument("project")
    p_gen.add_argument("--from-design-spec", action="store_true")

    p_val = sub.add_parser("validate")
    p_val.add_argument("project")

    p_diff = sub.add_parser("diff")
    p_diff.add_argument("old")
    p_diff.add_argument("new")

    p_re = sub.add_parser("renumber")
    p_re.add_argument("project")
    p_re.add_argument("--start", type=int, default=1)

    p_touch = sub.add_parser("touch")
    p_touch.add_argument("project")
    p_touch.add_argument("--slides", required=True)

    p_dump = sub.add_parser("dump")
    p_dump.add_argument("project")

    args = p.parse_args()

    if args.cmd == "generate":
        outline = generate(Path(args.project), from_design_spec=args.from_design_spec)
        out_path = save(Path(args.project), outline)
        print(f"✓ wrote {out_path} ({len(outline['slides'])} slides)")
        return 0

    if args.cmd == "validate":
        errors = validate(Path(args.project))
        for e in errors:
            print(f"  ✖ {e}")
        if errors:
            print(f"\n{len(errors)} error(s).")
            return 1
        print("✓ outline.yaml valid")
        return 0

    if args.cmd == "diff":
        old = yaml.safe_load(Path(args.old).read_text(encoding="utf-8")) or {}
        new = yaml.safe_load(Path(args.new).read_text(encoding="utf-8")) or {}
        d = diff(old, new)
        json.dump(d, sys.stdout, indent=2, ensure_ascii=False)
        sys.stdout.write("\n")
        return 0

    if args.cmd == "renumber":
        m = renumber(Path(args.project), start=args.start)
        for k, v in m.items():
            print(f"  {k} → {v}")
        if not m:
            print("(no renames needed)")
        return 0

    if args.cmd == "touch":
        ids = [s.strip() for s in args.slides.split(",") if s.strip()]
        n = touch(Path(args.project), ids)
        print(f"✓ marked {n} slide(s) dirty")
        return 0

    if args.cmd == "dump":
        outline = load(Path(args.project))
        json.dump(outline, sys.stdout, indent=2, ensure_ascii=False)
        sys.stdout.write("\n")
        return 0

    return 2


if __name__ == "__main__":
    sys.exit(_cli())
