#!/usr/bin/env python3
"""
PPT Master - 4-unit slide regeneration.

Modes:
  --slides ID,ID,...   regenerate exactly these slide ids
  --sections ID,ID,... regenerate every slide in the named sections
  --theme              re-finalize all slides with current theme overrides
                       (no LLM call; only token re-resolution)
  --reorganize         honour outline.yaml's current slide order (renumber)
                       and finalize newly-added slides

In all four modes the steps are:
  1. Touch outline.yaml dirty flags for the affected slide ids.
  2. (Slides/Sections/Reorganize only) ask the user / Executor to re-emit
     SVGs into svg_output/ for the dirty slides. This script does NOT call
     the LLM; it prints a TO-DO list naming the slides that still need an
     Executor pass. The editor UI integrates this by hand-off.
  3. Run finalize_svg with --slides <dirty list> to embed components and
     resolve tokens (cheap; no LLM).
  4. Re-export PPTX from svg_final/ (always full rebuild for v1).
  5. Clear dirty flags and bump last_finalized timestamps.

Theme mode skips step 2 entirely — the SVGs in svg_output/ already use token
references; finalize re-resolves them with new theme_overrides.

Usage:
    python3 slide_regenerator.py <project> --slides 03_m27,04_music
    python3 slide_regenerator.py <project> --sections products
    python3 slide_regenerator.py <project> --theme
    python3 slide_regenerator.py <project> --reorganize
"""

from __future__ import annotations

import argparse
import datetime
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import outline_manager  # type: ignore


SCRIPTS = Path(__file__).parent


def _resolve_design_md(project_dir: Path) -> Path | None:
    """Mirror finalize_svg's resolution but expose to caller."""
    local = project_dir / "design_system.md"
    if local.exists():
        return local
    pointer = project_dir / ".ppt-master" / "template.txt"
    if pointer.exists():
        slug = pointer.read_text(encoding="utf-8").strip()
        cand = SCRIPTS.parent / "templates" / "layouts" / slug / "DESIGN.md"
        if cand.exists():
            return cand
    return None


def _design_with_overrides(project_dir: Path) -> Path | None:
    """If theme_overrides exist, materialize an effective DESIGN.md to a temp
    file inside the project so finalize_svg picks it up."""
    outline = outline_manager.load(project_dir)
    overrides = (outline or {}).get("theme_overrides") or {}
    base = _resolve_design_md(project_dir)
    if not base:
        return None
    if not overrides:
        return base

    # Apply overrides as token-table edits inside a copy of DESIGN.md.
    text = base.read_text(encoding="utf-8")
    color_overrides = overrides.get("colors") or {}
    for tok, hex_value in color_overrides.items():
        # Replace only the first occurrence of "| <tok> | <hex> |" in any color table.
        import re
        pattern = re.compile(rf"(\|\s*{re.escape(tok)}\s*\|\s*)#[0-9a-fA-F]{{3,8}}", re.IGNORECASE)
        text, n = pattern.subn(rf"\g<1>{hex_value}", text, count=1)
        if n == 0:
            # Token not in palette table; append a row to "### Brand & Accent" if present.
            text = text.replace(
                "### Brand & Accent",
                f"### Brand & Accent\n<!-- override -->\n| {tok} | {hex_value} | override | added |",
                1,
            )

    out_path = project_dir / ".effective-design.md"
    out_path.write_text(text, encoding="utf-8")
    return out_path


def _pending_executor_ids(project_dir: Path, dirty_ids: list[str]) -> list[str]:
    """Slides marked dirty whose SVG in svg_output/ does not exist yet."""
    svg_output = project_dir / "svg_output"
    pending: list[str] = []
    for sid in dirty_ids:
        if not any(svg_output.glob(f"{sid}*.svg")):
            pending.append(sid)
    return pending


def _run(cmd: list[str], cwd: Path | None = None) -> int:
    print("→", " ".join(str(c) for c in cmd))
    return subprocess.run(cmd, cwd=cwd).returncode


def _finalize(project_dir: Path, slide_ids: list[str] | None, design_path: Path | None) -> int:
    cmd = ["python3", str(SCRIPTS / "finalize_svg.py"), str(project_dir), "--quiet"]
    if slide_ids:
        cmd += ["--slides", ",".join(slide_ids)]
    if design_path:
        cmd += ["--design", str(design_path)]
    return _run(cmd)


def _export_pptx(project_dir: Path) -> int:
    cmd = ["python3", str(SCRIPTS / "svg_to_pptx.py"), str(project_dir), "-s", "final"]
    return _run(cmd)


def _mark_finalized(project_dir: Path, slide_ids: list[str]) -> None:
    outline = outline_manager.load(project_dir)
    if not outline:
        return
    today = datetime.date.today().isoformat()
    for slide in outline.get("slides", []):
        if slide["id"] in slide_ids:
            slide["dirty"] = False
            slide["last_finalized"] = today
    outline_manager.save(project_dir, outline)


# ---------------------------------------------------------------------------
# 4 modes
# ---------------------------------------------------------------------------

def regen_slides(project_dir: Path, slide_ids: list[str]) -> int:
    outline_manager.touch(project_dir, slide_ids)
    pending = _pending_executor_ids(project_dir, slide_ids)
    if pending:
        print("ℹ Executor must emit SVGs for: " + ", ".join(pending))
        print("  (Use the editor's 'regenerate via LLM' button or run the Executor manually.)")
        # Still finalize whatever exists.
    design = _design_with_overrides(project_dir)
    available = [s for s in slide_ids if s not in pending]
    if available:
        rc = _finalize(project_dir, available, design)
        if rc != 0:
            return rc
    rc = _export_pptx(project_dir)
    if rc == 0 and available:
        _mark_finalized(project_dir, available)
    return rc


def regen_sections(project_dir: Path, section_ids: list[str]) -> int:
    outline = outline_manager.load(project_dir)
    if not outline:
        print("✖ outline.yaml missing; run outline_manager.py generate first.")
        return 1
    sec_index = {s["id"]: s for s in outline.get("sections", [])}
    slide_ids: list[str] = []
    for sid in section_ids:
        if sid not in sec_index:
            print(f"✖ Unknown section: {sid!r}")
            return 1
        slide_ids.extend(sec_index[sid].get("slides", []))
    return regen_slides(project_dir, slide_ids)


def regen_theme(project_dir: Path) -> int:
    """Re-finalize every slide using the (possibly overridden) DESIGN.md.

    No LLM call; the Executor's emitted SVGs are reused as-is and only the
    token resolver runs again.
    """
    design = _design_with_overrides(project_dir)
    rc = _finalize(project_dir, slide_ids=None, design_path=design)
    if rc != 0:
        return rc
    rc = _export_pptx(project_dir)
    if rc == 0:
        outline = outline_manager.load(project_dir)
        all_ids = [s["id"] for s in outline.get("slides", [])]
        _mark_finalized(project_dir, all_ids)
    return rc


def regen_reorganize(project_dir: Path) -> int:
    """Apply outline.yaml ordering: rename SVG/notes files, then finalize."""
    rename = outline_manager.renumber(project_dir)
    if rename:
        print(f"Renamed {len(rename)} slide(s):")
        for k, v in rename.items():
            print(f"  {k} → {v}")
    # After renumbering, every slide present in svg_output must be re-finalized.
    outline = outline_manager.load(project_dir)
    pending = _pending_executor_ids(project_dir, [s["id"] for s in outline.get("slides", [])])
    if pending:
        print("ℹ Executor must emit SVGs for new slides: " + ", ".join(pending))
    design = _design_with_overrides(project_dir)
    rc = _finalize(project_dir, slide_ids=None, design_path=design)
    if rc != 0:
        return rc
    rc = _export_pptx(project_dir)
    if rc == 0:
        all_ids = [s["id"] for s in outline.get("slides", [])]
        _mark_finalized(project_dir, [s for s in all_ids if s not in pending])
    return rc


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _cli() -> int:
    p = argparse.ArgumentParser(description="Regenerate slides at slide / section / theme / outline scope.")
    p.add_argument("project", type=Path)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--slides", help="Comma-separated slide ids")
    g.add_argument("--sections", help="Comma-separated section ids")
    g.add_argument("--theme", action="store_true", help="Re-finalize all slides with current theme_overrides")
    g.add_argument("--reorganize", action="store_true", help="Apply outline.yaml order; finalize all")
    args = p.parse_args()

    if not args.project.exists():
        print(f"✖ Project not found: {args.project}")
        return 1

    if args.slides:
        ids = [s.strip() for s in args.slides.split(",") if s.strip()]
        return regen_slides(args.project, ids)
    if args.sections:
        ids = [s.strip() for s in args.sections.split(",") if s.strip()]
        return regen_sections(args.project, ids)
    if args.theme:
        return regen_theme(args.project)
    if args.reorganize:
        return regen_reorganize(args.project)
    return 2


if __name__ == "__main__":
    sys.exit(_cli())
