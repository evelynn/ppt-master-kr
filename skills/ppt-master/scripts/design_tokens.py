#!/usr/bin/env python3
"""
PPT Master - DESIGN.md token parser and resolver.

Parses a layout template's DESIGN.md (per references/design-md-spec.md) into a
DesignSystem object and resolves {token} references inside SVG / Markdown text.

Public API:
    parse_design_md(path) -> DesignSystem
    DesignSystem.resolve(text, *, canvas=None) -> str
    DesignSystem.swap(palette={...}, typography={...}) -> DesignSystem
    validate(path) -> list[str]   # error messages, empty list if OK
    lint_svg(svg_path, design_path) -> list[str]

CLI:
    python3 design_tokens.py validate <DESIGN.md>
    python3 design_tokens.py resolve <text-or-file> --design <DESIGN.md>
    python3 design_tokens.py lint-svg <slide.svg> --design <DESIGN.md>
    python3 design_tokens.py dump <DESIGN.md>     # JSON dump for editor UI
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Iterator


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

REQUIRED_SECTIONS = [
    "Overview",
    "Colors",
    "Typography",
    "Layout",
    "Elevation & Depth",
    "Shapes",
    "Components",
    "Slide Templates",
    "Do's and Don'ts",
    "Canvas Variants",
    "Known Gaps",
]


@dataclass
class TypographyToken:
    name: str
    size_px: float
    weight: int = 400
    line_height: float = 1.4
    letter_spacing: str = "0"
    use: str = ""

    @property
    def size_pt(self) -> float:
        return round(self.size_px / 1.333, 1)


@dataclass
class ComponentSpec:
    name: str           # "product-cards/coral"
    section: str        # raw markdown body for this component
    slots: list[str] = field(default_factory=list)
    default_width: float = 0
    default_height: float = 0


@dataclass
class CanvasSpec:
    name: str
    viewbox: str
    margin_top: float
    margin_right: float
    margin_bottom: float
    margin_left: float
    grid_columns: int
    gutter: float


@dataclass
class DesignSystem:
    path: Path
    overview: str = ""
    colors: dict[str, str] = field(default_factory=dict)            # name -> hex
    color_meta: dict[str, dict[str, str]] = field(default_factory=dict)
    fonts: dict[str, str] = field(default_factory=dict)             # heading/body/code -> family stack
    typography: dict[str, TypographyToken] = field(default_factory=dict)
    spacing: dict[str, float] = field(default_factory=dict)         # px
    rounded: dict[str, float] = field(default_factory=dict)         # px
    elevation: dict[str, str] = field(default_factory=dict)         # token -> raw filter SVG snippet
    elevation_filters: dict[str, str] = field(default_factory=dict) # filter id -> raw filter element
    canvases: dict[str, CanvasSpec] = field(default_factory=dict)
    components: dict[str, ComponentSpec] = field(default_factory=dict)
    slide_templates: dict[str, str] = field(default_factory=dict)
    do_dont: dict[str, list[str]] = field(default_factory=dict)
    canvas_variants: dict[str, dict[str, str]] = field(default_factory=dict)
    known_gaps: list[str] = field(default_factory=list)
    raw_sections: dict[str, str] = field(default_factory=dict)

    # ---- token resolution -------------------------------------------------

    _TOKEN_RE = re.compile(r"\{(?P<ns>[a-z][a-z0-9]*)\.(?P<name>[a-z0-9-]+)(?:\.(?P<attr>[a-z_]+))?\}")

    def resolve(self, text: str, canvas: str | None = None, _depth: int = 0) -> str:
        """Resolve all {namespace.name[.attr]} tokens in text.

        Recursive: if a resolved value contains tokens, they are resolved too,
        capped at depth 6 to avoid cycles.
        """
        if not isinstance(text, str) or _depth > 6 or "{" not in text:
            return text

        def repl(m: re.Match[str]) -> str:
            ns, name, attr = m.group("ns"), m.group("name"), m.group("attr")
            try:
                value = self._lookup(ns, name, attr, canvas)
            except KeyError:
                return m.group(0)  # leave unresolved for the linter to find
            if isinstance(value, float) and value.is_integer():
                return str(int(value))
            # Tokens are typically substituted into SVG attribute values that
            # are wrapped in double quotes. Escape any inner double quotes so
            # values like font-family stacks (`"DM Sans", "Inter", ...`) stay
            # well-formed XML.
            text_value = str(value)
            if '"' in text_value:
                text_value = text_value.replace('"', '&quot;')
            return text_value

        out = self._TOKEN_RE.sub(repl, text)
        if out != text and "{" in out:
            return self.resolve(out, canvas=canvas, _depth=_depth + 1)
        return out

    def _lookup(self, ns: str, name: str, attr: str | None, canvas: str | None) -> Any:
        # Canvas variant override takes precedence when canvas is set.
        if canvas and canvas in self.canvas_variants:
            override = self.canvas_variants[canvas].get(f"{ns}.{name}" if attr is None else f"{ns}.{name}.{attr}")
            if override is not None:
                return override

        if ns == "colors":
            return self.colors[name]
        if ns == "spacing":
            return self.spacing[name]
        if ns == "rounded":
            return self.rounded[name]
        if ns == "elevation":
            return self.elevation[name]
        if ns == "font":
            return self.fonts[name]
        if ns == "typography":
            tok = self.typography[name]
            if attr in (None, "size", "px"):
                return tok.size_px
            if attr == "pt":
                return tok.size_pt
            if attr == "weight":
                return tok.weight
            if attr in ("line_height", "lh"):
                return tok.line_height
            if attr in ("letter_spacing", "ls"):
                return tok.letter_spacing
            raise KeyError((ns, name, attr))
        raise KeyError((ns, name, attr))

    # ---- mutation ---------------------------------------------------------

    def swap(self, *, palette: dict[str, str] | None = None,
             typography: dict[str, TypographyToken] | None = None) -> "DesignSystem":
        """Return a copy with selected token tables overridden.

        Used by the editor's "theme swap" action — no LLM call required.
        """
        new = DesignSystem(
            path=self.path,
            overview=self.overview,
            colors=dict(self.colors),
            color_meta=dict(self.color_meta),
            fonts=dict(self.fonts),
            typography=dict(self.typography),
            spacing=dict(self.spacing),
            rounded=dict(self.rounded),
            elevation=dict(self.elevation),
            elevation_filters=dict(self.elevation_filters),
            canvases=dict(self.canvases),
            components=dict(self.components),
            slide_templates=dict(self.slide_templates),
            do_dont=dict(self.do_dont),
            canvas_variants=dict(self.canvas_variants),
            known_gaps=list(self.known_gaps),
            raw_sections=dict(self.raw_sections),
        )
        if palette:
            for k, v in palette.items():
                new.colors[k] = v
        if typography:
            for k, v in typography.items():
                new.typography[k] = v
        return new

    def to_json(self) -> dict[str, Any]:
        """Serializable snapshot for the editor UI."""
        return {
            "path": str(self.path),
            "overview": self.overview,
            "colors": self.colors,
            "color_meta": self.color_meta,
            "fonts": self.fonts,
            "typography": {k: asdict(v) | {"size_pt": v.size_pt} for k, v in self.typography.items()},
            "spacing": self.spacing,
            "rounded": self.rounded,
            "elevation": self.elevation,
            "canvases": {k: asdict(v) for k, v in self.canvases.items()},
            "components": {k: {"name": v.name, "slots": v.slots,
                                "default_width": v.default_width,
                                "default_height": v.default_height}
                            for k, v in self.components.items()},
            "slide_templates": list(self.slide_templates.keys()),
            "do_dont": self.do_dont,
            "canvas_variants": self.canvas_variants,
            "known_gaps": self.known_gaps,
        }


# ---------------------------------------------------------------------------
# Markdown parsing
# ---------------------------------------------------------------------------

_HEX_RE = re.compile(r"#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})\b")
_INT_RE = re.compile(r"-?\d+(?:\.\d+)?")


def _split_sections(text: str) -> dict[str, str]:
    """Split a markdown doc by `## Heading` lines.

    Sub-headings (`### foo`) stay inside their parent section.
    """
    sections: dict[str, str] = {}
    current: str | None = None
    buf: list[str] = []
    for line in text.splitlines():
        m = re.match(r"^##\s+(?!#)(.+?)\s*$", line)
        if m:
            if current is not None:
                sections[current] = "\n".join(buf).strip()
            current = m.group(1).strip()
            buf = []
        else:
            buf.append(line)
    if current is not None:
        sections[current] = "\n".join(buf).strip()
    return sections


def _iter_table_rows(section: str) -> Iterator[list[str]]:
    """Yield non-header rows from every markdown pipe-table in section."""
    in_table = False
    saw_separator = False
    for line in section.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            in_table = False
            saw_separator = False
            continue
        # Skip header-separator lines like |---|---|
        if re.match(r"^\|[\s\-:|]+\|\s*$", stripped):
            in_table = True
            saw_separator = True
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if not in_table or not saw_separator:
            # This is the header row of a new table; remember we're inside one.
            in_table = True
            continue
        yield cells


def _parse_colors(section: str) -> tuple[dict[str, str], dict[str, dict[str, str]]]:
    colors: dict[str, str] = {}
    meta: dict[str, dict[str, str]] = {}
    for cells in _iter_table_rows(section):
        if len(cells) < 2:
            continue
        token = cells[0].lower().strip()
        if not re.match(r"^[a-z][a-z0-9-]*$", token):
            continue
        hex_match = _HEX_RE.search(cells[1])
        if not hex_match:
            continue
        colors[token] = hex_match.group(0)
        meta[token] = {
            "role": cells[2] if len(cells) > 2 else "",
            "usage": cells[3] if len(cells) > 3 else "",
        }
    return colors, meta


def _parse_typography(section: str) -> tuple[dict[str, str], dict[str, TypographyToken]]:
    fonts: dict[str, str] = {}
    typography: dict[str, TypographyToken] = {}

    for line in section.splitlines():
        m = re.match(r"\*\*(Heading|Body|Code|Display) family\*\*:\s*(.+)", line.strip())
        if m:
            fonts[m.group(1).lower()] = m.group(2).strip()

    for cells in _iter_table_rows(section):
        if len(cells) < 2:
            continue
        token = cells[0].lower().strip()
        if not re.match(r"^[a-z][a-z0-9-]*$", token):
            continue
        size_match = _INT_RE.search(cells[1])
        if not size_match:
            continue
        size_px = float(size_match.group(0))
        weight = 400
        line_height = 1.4
        letter_spacing = "0"
        use = ""
        if len(cells) > 2:
            wm = _INT_RE.search(cells[2])
            if wm:
                weight = int(float(wm.group(0)))
        if len(cells) > 3:
            lhm = _INT_RE.search(cells[3])
            if lhm:
                line_height = float(lhm.group(0))
        if len(cells) > 4:
            letter_spacing = cells[4] or "0"
        if len(cells) > 5:
            use = cells[5]
        typography[token] = TypographyToken(
            name=token, size_px=size_px, weight=weight,
            line_height=line_height, letter_spacing=letter_spacing, use=use,
        )
    return fonts, typography


def _parse_scale_table(section: str) -> dict[str, float]:
    """Parse a 2-column |token|px| scale table."""
    out: dict[str, float] = {}
    for cells in _iter_table_rows(section):
        if len(cells) < 2:
            continue
        token = cells[0].lower().strip()
        if not re.match(r"^[a-z0-9][a-z0-9-]*$", token):
            continue
        m = _INT_RE.search(cells[1])
        if not m:
            continue
        out[token] = float(m.group(0))
    return out


def _parse_layout(section: str) -> tuple[dict[str, CanvasSpec], dict[str, float]]:
    canvases: dict[str, CanvasSpec] = {}
    spacing: dict[str, float] = {}

    # Find sub-section markers ### Canvas vs ### Spacing scale
    blocks = re.split(r"\n###\s+", "\n" + section)
    # blocks[0] is preamble, rest are "<sub-heading>\n<body>"
    for block in blocks[1:]:
        sub_lines = block.split("\n", 1)
        sub = sub_lines[0].strip().lower()
        body = sub_lines[1] if len(sub_lines) > 1 else ""
        if "canvas" in sub:
            for cells in _iter_table_rows(body):
                if len(cells) < 5:
                    continue
                fmt = cells[0].strip()
                viewbox = cells[1].strip().strip("`")
                margins = re.findall(r"\d+(?:\.\d+)?", cells[2])
                if len(margins) < 4:
                    continue
                grid_match = _INT_RE.search(cells[3])
                gutter_match = _INT_RE.search(cells[4])
                if not grid_match or not gutter_match:
                    continue
                canvases[fmt] = CanvasSpec(
                    name=fmt, viewbox=viewbox,
                    margin_top=float(margins[0]),
                    margin_right=float(margins[1]),
                    margin_bottom=float(margins[2]),
                    margin_left=float(margins[3]),
                    grid_columns=int(float(grid_match.group(0))),
                    gutter=float(gutter_match.group(0)),
                )
        elif "spacing" in sub:
            spacing.update(_parse_scale_table(body))
    return canvases, spacing


def _parse_elevation(section: str) -> tuple[dict[str, str], dict[str, str]]:
    tokens: dict[str, str] = {}
    for cells in _iter_table_rows(section):
        if len(cells) < 3:
            continue
        token = cells[0].strip().lower()
        m = re.match(r"^elevation\.([a-z0-9-]+)$", token)
        if not m:
            continue
        # Effect SVG implementation column
        impl = cells[2]
        # Extract filter URL ref or "(no filter ...)" string
        url_match = re.search(r"url\(#([a-z0-9-]+)\)", impl)
        if url_match:
            tokens[m.group(1)] = f'filter="url(#{url_match.group(1)})"'
        else:
            tokens[m.group(1)] = ""
    # Capture <filter id="..."> blocks for later injection
    filters: dict[str, str] = {}
    for fm in re.finditer(r'(<filter\s+id="([^"]+)"[^>]*>.*?</filter>)', section, re.DOTALL):
        filters[fm.group(2)] = fm.group(1)
    return tokens, filters


def _parse_shapes(section: str) -> dict[str, float]:
    rounded: dict[str, float] = {}
    blocks = re.split(r"\n###\s+", "\n" + section)
    for block in blocks[1:]:
        sub_lines = block.split("\n", 1)
        sub = sub_lines[0].strip().lower()
        body = sub_lines[1] if len(sub_lines) > 1 else ""
        if "rounded" in sub:
            rounded.update(_parse_scale_table(body))
    return rounded


def _parse_components(section: str) -> dict[str, ComponentSpec]:
    components: dict[str, ComponentSpec] = {}
    blocks = re.split(r"\n###\s+", "\n" + section)
    for block in blocks[1:]:
        head, _, body = block.partition("\n")
        name = head.strip()
        if "/" not in name:
            continue
        slots = []
        for slot_match in re.finditer(r"`data-([a-z0-9_-]+)`", body):
            sid = slot_match.group(1)
            if sid not in slots:
                slots.append(sid)
        size_match = re.search(r"Default size.*?(\d+)\s*[x×]\s*(\d+)", body, re.IGNORECASE)
        dw = float(size_match.group(1)) if size_match else 0
        dh = float(size_match.group(2)) if size_match else 0
        components[name] = ComponentSpec(
            name=name, section=body.strip(),
            slots=slots, default_width=dw, default_height=dh,
        )
    return components


def _parse_slide_templates(section: str) -> dict[str, str]:
    templates: dict[str, str] = {}
    blocks = re.split(r"\n###\s+", "\n" + section)
    for block in blocks[1:]:
        head, _, body = block.partition("\n")
        templates[head.strip()] = body.strip()
    return templates


def _parse_do_dont(section: str) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {"do": [], "dont": []}
    bucket: str | None = None
    for line in section.splitlines():
        s = line.strip()
        if re.match(r"^###\s+Do\b", s, re.IGNORECASE):
            bucket = "do"
        elif re.match(r"^###\s+Don'?t\b", s, re.IGNORECASE):
            bucket = "dont"
        elif bucket and s.startswith("- "):
            out[bucket].append(s[2:].strip())
    return out


def _parse_canvas_variants(section: str) -> dict[str, dict[str, str]]:
    """Returns {canvas_name: {dotted-token-path: override-value}}."""
    rows = list(_iter_table_rows(section))
    if not rows:
        return {}
    header_match = None
    for line in section.splitlines():
        s = line.strip()
        if s.startswith("|") and "format" not in s.lower():
            # Look for a header row like "| Element | ppt169 | ppt43 | Notes |"
            cells = [c.strip().lower() for c in s.strip("|").split("|")]
            if any("ppt" in c or c in ("ppt169", "ppt43") for c in cells):
                header_match = cells
                break
    if not header_match:
        return {}
    canvas_names = [c for c in header_match[1:] if c.startswith("ppt") or c in ("ppt169", "ppt43")]
    out: dict[str, dict[str, str]] = {c: {} for c in canvas_names}
    for cells in rows:
        if len(cells) < 1 + len(canvas_names):
            continue
        elem_label = cells[0].lower().strip().replace(" ", "-")
        for i, c in enumerate(canvas_names, start=1):
            val = cells[i].strip()
            if val:
                out[c][elem_label] = val
    return out


# ---------------------------------------------------------------------------
# Top-level loader
# ---------------------------------------------------------------------------

def parse_design_md(path: str | Path) -> DesignSystem:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    sections = _split_sections(text)
    ds = DesignSystem(path=p, raw_sections=sections)

    ds.overview = sections.get("Overview", "")

    if "Colors" in sections:
        ds.colors, ds.color_meta = _parse_colors(sections["Colors"])
    if "Typography" in sections:
        ds.fonts, ds.typography = _parse_typography(sections["Typography"])
    if "Layout" in sections:
        ds.canvases, ds.spacing = _parse_layout(sections["Layout"])
    if "Elevation & Depth" in sections:
        ds.elevation, ds.elevation_filters = _parse_elevation(sections["Elevation & Depth"])
    if "Shapes" in sections:
        ds.rounded = _parse_shapes(sections["Shapes"])
    if "Components" in sections:
        ds.components = _parse_components(sections["Components"])
    if "Slide Templates" in sections:
        ds.slide_templates = _parse_slide_templates(sections["Slide Templates"])
    if "Do's and Don'ts" in sections:
        ds.do_dont = _parse_do_dont(sections["Do's and Don'ts"])
    if "Canvas Variants" in sections:
        ds.canvas_variants = _parse_canvas_variants(sections["Canvas Variants"])
    if "Known Gaps" in sections:
        ds.known_gaps = [
            line[2:].strip()
            for line in sections["Known Gaps"].splitlines()
            if line.strip().startswith("- ")
        ]

    return ds


# ---------------------------------------------------------------------------
# Validation and linting
# ---------------------------------------------------------------------------

def validate(path: str | Path) -> list[str]:
    errors: list[str] = []
    p = Path(path)
    if not p.exists():
        return [f"DESIGN.md not found: {p}"]

    text = p.read_text(encoding="utf-8")
    sections = _split_sections(text)
    for required in REQUIRED_SECTIONS:
        if required not in sections:
            errors.append(f"Missing required section: ## {required}")

    ds = parse_design_md(p)

    if not ds.colors:
        errors.append("No color tokens parsed; check the `## Colors` table format.")
    if not ds.typography:
        errors.append("No typography tokens parsed; check the `## Typography` Hierarchy table.")

    # Token reference integrity
    for tok in ds.colors.values():
        if not _HEX_RE.fullmatch(tok):
            errors.append(f"Color value not a valid hex: {tok}")
    for k, v in ds.typography.items():
        if v.weight < 100 or v.weight > 900:
            errors.append(f"Typography '{k}' has invalid weight {v.weight}")
        if v.size_px <= 0:
            errors.append(f"Typography '{k}' has non-positive size {v.size_px}")

    # Component file existence (only if templates/components exists)
    components_dir = p.parent.parent.parent / "components"
    if components_dir.exists():
        for comp_name in ds.components:
            comp_file = components_dir / f"{comp_name}.svg"
            if not comp_file.exists():
                errors.append(f"Component '{comp_name}' has no SVG at {comp_file}")

    # Self-references inside DESIGN.md must resolve.
    self_refs = ds._TOKEN_RE.findall(text)
    for ns, name, attr in self_refs:
        try:
            ds._lookup(ns, name, attr or None, canvas=None)
        except KeyError:
            errors.append(f"Unresolved token in DESIGN.md: {{{ns}.{name}{('.' + attr) if attr else ''}}}")

    return errors


def lint_svg(svg_path: str | Path, design_path: str | Path) -> list[str]:
    sp = Path(svg_path)
    dp = Path(design_path)
    text = sp.read_text(encoding="utf-8")
    if "<!-- design-md:freehex -->" in text:
        return []
    ds = parse_design_md(dp)
    palette = {v.upper() for v in ds.colors.values()}
    issues: list[str] = []
    for m in _HEX_RE.finditer(text):
        hexval = m.group(0).upper()
        # Normalize 3-digit shorthand
        if len(hexval) == 4:
            hexval = "#" + "".join(ch * 2 for ch in hexval[1:])
        if hexval not in palette:
            line = text.count("\n", 0, m.start()) + 1
            issues.append(f"{sp}:{line}: hex {m.group(0)} not in DESIGN.md palette")
    # Unresolved tokens
    for m in ds._TOKEN_RE.finditer(text):
        ns, name, attr = m.group("ns"), m.group("name"), m.group("attr")
        try:
            ds._lookup(ns, name, attr, canvas=None)
        except KeyError:
            line = text.count("\n", 0, m.start()) + 1
            issues.append(f"{sp}:{line}: unresolved token {m.group(0)}")
    return issues


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _cli() -> int:
    parser = argparse.ArgumentParser(description="DESIGN.md token utilities")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_validate = sub.add_parser("validate", help="Validate a DESIGN.md")
    p_validate.add_argument("design")

    p_resolve = sub.add_parser("resolve", help="Resolve tokens in a string or file")
    p_resolve.add_argument("text")
    p_resolve.add_argument("--design", required=True)
    p_resolve.add_argument("--canvas")
    p_resolve.add_argument("--file", action="store_true",
                            help="Treat <text> as a file path")

    p_lint = sub.add_parser("lint-svg", help="Lint an SVG against a DESIGN.md palette")
    p_lint.add_argument("svg")
    p_lint.add_argument("--design", required=True)

    p_dump = sub.add_parser("dump", help="Dump parsed DESIGN.md as JSON")
    p_dump.add_argument("design")

    args = parser.parse_args()

    if args.cmd == "validate":
        errors = validate(args.design)
        if errors:
            for e in errors:
                print(f"  ✖ {e}")
            print(f"\n{len(errors)} validation error(s).")
            return 1
        print(f"✓ {args.design} is valid.")
        return 0

    if args.cmd == "resolve":
        ds = parse_design_md(args.design)
        text = Path(args.text).read_text(encoding="utf-8") if args.file else args.text
        sys.stdout.write(ds.resolve(text, canvas=args.canvas))
        return 0

    if args.cmd == "lint-svg":
        issues = lint_svg(args.svg, args.design)
        for i in issues:
            print(i)
        return 1 if issues else 0

    if args.cmd == "dump":
        ds = parse_design_md(args.design)
        json.dump(ds.to_json(), sys.stdout, indent=2, ensure_ascii=False, default=str)
        sys.stdout.write("\n")
        return 0

    return 2


if __name__ == "__main__":
    sys.exit(_cli())
