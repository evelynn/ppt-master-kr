#!/usr/bin/env python3
"""
PPT Master - SVG Component & Token embedder.

Two-step replacement run as the FIRST stage of finalize_svg:

1. Component embedding — replaces every
       <use data-component="category/name"
            data-<slot>="..." x=".." y=".." width=".." height=".." [fill=".." stroke=".."]/>
   with the contents of templates/components/<category>/<name>.svg, scaled to
   the requested box and with all `{{text.<slot>}}` placeholders substituted
   from the matching `data-<slot>` attribute.

2. Token resolution — substitutes every {colors.*}, {typography.*.attr},
   {rounded.*}, {spacing.*}, {elevation.*}, {font.*} reference using the
   layout's DESIGN.md (parsed via design_tokens.parse_design_md).

Slide templates (`<use data-slide-template="...">`) are NOT embedded here;
those are produced by the editor before SVG handoff and inlined directly.

Usage:
    from svg_finalize.embed_components import embed_components_in_text
    new_text = embed_components_in_text(svg_text, design_system, components_dir)
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree as ET


# ---------------------------------------------------------------------------
# Component embedding
# ---------------------------------------------------------------------------

# Match a self-closing or paired <use data-component="..."/> element.
# We use a regex (rather than full DOM parsing) so that we leave the rest of
# the SVG byte-identical and don't perturb whitespace or attribute ordering.
_USE_COMPONENT_RE = re.compile(
    r'<use\b(?P<attrs>[^>]*?\bdata-component=["\'][^"\']+["\'][^>]*?)/\s*>',
    re.DOTALL,
)
_ATTR_RE = re.compile(r'(\w[\w-]*)\s*=\s*"([^"]*)"')

# Match {{text.slot}} placeholders inside a component file.
_SLOT_RE = re.compile(r"\{\{\s*text\.([a-z0-9_-]+)\s*\}\}")


def _attrs_to_dict(attrs_str: str) -> dict[str, str]:
    return {m.group(1): m.group(2) for m in _ATTR_RE.finditer(attrs_str)}


def _strip_outer_svg(component_text: str) -> tuple[str, str]:
    """Return (inner_xml, viewBox) from a standalone component SVG file.

    The component file is `<svg viewBox="0 0 W H" ...>...</svg>`. We extract
    the children (everything between `>` of the opening tag and the closing
    `</svg>`) and the viewBox.
    """
    m = re.match(r'\s*<svg\b([^>]*)>(.*)</svg>\s*$', component_text, re.DOTALL)
    if not m:
        raise ValueError("component file is not a valid <svg>...</svg> document")
    open_attrs = m.group(1)
    inner = m.group(2)
    vb_match = re.search(r'viewBox=["\']([^"\']+)["\']', open_attrs)
    if not vb_match:
        raise ValueError("component <svg> is missing viewBox")
    return inner.strip(), vb_match.group(1)


def _embed_one(
    use_attrs: dict[str, str],
    components_dir: Path,
) -> str:
    """Build the replacement <g>...</g> markup for one <use data-component>."""
    name = use_attrs.get("data-component", "")
    if not name or "/" not in name:
        return ""

    component_path = components_dir / f"{name}.svg"
    if not component_path.exists():
        # Leave a comment so the lint pass can find missing components.
        return f"<!-- component-not-found:{name} -->"

    component_text = component_path.read_text(encoding="utf-8")
    inner, viewbox = _strip_outer_svg(component_text)
    vb_parts = viewbox.split()
    if len(vb_parts) != 4:
        return f"<!-- component-bad-viewbox:{name} -->"
    vb_w = float(vb_parts[2])
    vb_h = float(vb_parts[3])

    # Target placement
    x = float(use_attrs.get("x", 0))
    y = float(use_attrs.get("y", 0))
    w = float(use_attrs.get("width", vb_w))
    h = float(use_attrs.get("height", vb_h))

    sx = w / vb_w if vb_w else 1.0
    sy = h / vb_h if vb_h else 1.0

    # Substitute {{text.slot}} placeholders from data-<slot> attributes.
    # Empty slots collapse to empty string.
    def slot_repl(m: re.Match[str]) -> str:
        slot = m.group(1)
        return _xml_escape(use_attrs.get(f"data-{slot}", ""))

    body = _SLOT_RE.sub(slot_repl, inner)

    # Optional fill / stroke override applied to the outer <g>.
    extra = []
    for attr in ("fill", "stroke", "opacity", "fill-opacity", "stroke-opacity"):
        if attr in use_attrs and use_attrs[attr] not in ("", "none"):
            extra.append(f'{attr}="{use_attrs[attr]}"')
    extra_str = (" " + " ".join(extra)) if extra else ""

    transform = _format_transform(x, y, sx, sy)
    return (
        f'<g data-from-component="{name}" transform="{transform}"{extra_str}>'
        f"{body}"
        f"</g>"
    )


def _format_transform(x: float, y: float, sx: float, sy: float) -> str:
    parts: list[str] = []
    if x or y:
        parts.append(f"translate({_num(x)},{_num(y)})")
    if abs(sx - 1.0) > 1e-6 or abs(sy - 1.0) > 1e-6:
        if abs(sx - sy) < 1e-6:
            parts.append(f"scale({_num(sx)})")
        else:
            parts.append(f"scale({_num(sx)},{_num(sy)})")
    return " ".join(parts) or "translate(0,0)"


def _num(v: float) -> str:
    if abs(v - round(v)) < 1e-6:
        return str(int(round(v)))
    return f"{v:.4f}".rstrip("0").rstrip(".")


def _xml_escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
         .replace("<", "&lt;")
         .replace(">", "&gt;")
    )


def embed_components(svg_text: str, components_dir: Path) -> str:
    """Replace all <use data-component="..."/> elements in svg_text."""

    def repl(m: re.Match[str]) -> str:
        attrs = _attrs_to_dict(m.group("attrs"))
        return _embed_one(attrs, components_dir)

    return _USE_COMPONENT_RE.sub(repl, svg_text)


# ---------------------------------------------------------------------------
# Token resolution
# ---------------------------------------------------------------------------

def resolve_tokens(svg_text: str, design_system, canvas: str | None = None) -> str:
    """Resolve {colors.*}, {typography.*}, etc. via design_system.resolve()."""
    if design_system is None or "{" not in svg_text:
        return svg_text
    return design_system.resolve(svg_text, canvas=canvas)


# ---------------------------------------------------------------------------
# Combined entry point used by finalize_svg.py
# ---------------------------------------------------------------------------

def process_svg_text(
    svg_text: str,
    design_system=None,
    components_dir: Path | None = None,
    canvas: str | None = None,
) -> str:
    """Run component embedding + token resolution on one SVG document."""
    text = svg_text
    if components_dir and components_dir.exists():
        text = embed_components(text, components_dir)
    if design_system is not None:
        text = resolve_tokens(text, design_system, canvas=canvas)
    return text


def process_svg_file(
    svg_path: Path,
    design_system=None,
    components_dir: Path | None = None,
    canvas: str | None = None,
    out_path: Path | None = None,
) -> Path:
    """Process one SVG file in place (or to out_path)."""
    src = Path(svg_path)
    text = src.read_text(encoding="utf-8")
    new_text = process_svg_text(text, design_system, components_dir, canvas)
    dst = Path(out_path) if out_path else src
    dst.write_text(new_text, encoding="utf-8")
    return dst


# ---------------------------------------------------------------------------
# CLI for ad-hoc debugging
# ---------------------------------------------------------------------------

def _cli() -> int:
    import argparse, sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from design_tokens import parse_design_md  # type: ignore

    p = argparse.ArgumentParser(description="Embed components and resolve DESIGN.md tokens in an SVG.")
    p.add_argument("svg", help="Path to slide SVG")
    p.add_argument("--design", required=True, help="Path to DESIGN.md")
    p.add_argument("--components-dir", default=None,
                    help="Path to templates/components/ (default: auto-detect from DESIGN.md path)")
    p.add_argument("--canvas", default=None)
    p.add_argument("--in-place", action="store_true")
    args = p.parse_args()

    ds = parse_design_md(args.design)
    if args.components_dir:
        comp_dir = Path(args.components_dir)
    else:
        # Default: <design_md_dir>/../../components
        comp_dir = Path(args.design).parent.parent.parent / "components"

    out = process_svg_file(
        Path(args.svg),
        design_system=ds,
        components_dir=comp_dir,
        canvas=args.canvas,
        out_path=None if args.in_place else Path(args.svg).with_suffix(".embedded.svg"),
    )
    print(f"✓ wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
