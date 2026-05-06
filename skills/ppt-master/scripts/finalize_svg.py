#!/usr/bin/env python3
"""
PPT Master - SVG Post-processing Tool (Unified Entry Point)

Processes SVG files from svg_output/ and outputs them to svg_final/.
By default, all processing steps are executed. You can also specify
individual steps via arguments.

Usage:
    # Execute all processing steps (recommended)
    python3 scripts/finalize_svg.py <project_directory>

    # Execute only specific steps
    python3 scripts/finalize_svg.py <project_directory> --only embed-icons fix-rounded

Examples:
    python3 scripts/finalize_svg.py projects/my_project
    python3 scripts/finalize_svg.py examples/ppt169_demo --only embed-icons

Processing options:
    embed-icons   - Replace <use data-icon="..."/> with actual icon SVG
    crop-images   - Smart crop images based on preserveAspectRatio="slice"
    fix-aspect    - Fix image aspect ratio (prevent stretching during PPT shape conversion)
    embed-images  - Convert external images to Base64 embedded
    flatten-text  - Convert <tspan> to independent <text> (for special renderers)
    fix-rounded   - Convert <rect rx="..."/> to <path> (for PPT shape conversion)
"""

import os
import sys
import shutil
import argparse
from pathlib import Path

# Import finalize helpers from the internal package.
sys.path.insert(0, str(Path(__file__).parent))
from svg_finalize.crop_images import process_svg_images as crop_images_in_svg
from svg_finalize.embed_components import process_svg_text as process_components_and_tokens
from svg_finalize.embed_icons import process_svg_file as embed_icons_in_file
from svg_finalize.embed_images import embed_images_in_svg
from svg_finalize.fix_image_aspect import fix_image_aspect_in_svg

try:
    from i18n import t
except ImportError:
    def t(key, **kwargs):  # type: ignore
        return key


def _resolve_design_md(project_dir: Path, explicit: str | None) -> Path | None:
    """Locate the DESIGN.md to apply to this project.

    Priority:
      1. Explicit --design CLI flag.
      2. <project>/design_system.md (project-level override).
      3. <project>/.ppt-master/template.txt: name → templates/layouts/<name>/DESIGN.md
      4. None (no token resolution; backwards-compatible behaviour).
    """
    if explicit:
        p = Path(explicit)
        return p if p.exists() else None
    local = project_dir / "design_system.md"
    if local.exists():
        return local
    pointer = project_dir / ".ppt-master" / "template.txt"
    if pointer.exists():
        slug = pointer.read_text(encoding="utf-8").strip()
        cand = (Path(__file__).parent.parent / "templates" / "layouts" / slug / "DESIGN.md")
        if cand.exists():
            return cand
    return None


def _load_design_system(design_md_path: Path | None):
    if design_md_path is None:
        return None
    try:
        from design_tokens import parse_design_md
        return parse_design_md(design_md_path)
    except Exception as e:  # pragma: no cover - non-fatal
        safe_print(f"[WARN] Failed to parse DESIGN.md ({design_md_path}): {e}")
        return None


def process_components_and_tokens_in_file(
    svg_file: Path,
    design_system,
    components_dir: Path,
    canvas: str | None = None,
    verbose: bool = False,
) -> bool:
    """Run component embed + token resolution on one file. Returns True if any change."""
    try:
        original = svg_file.read_text(encoding="utf-8")
        new_text = process_components_and_tokens(
            original,
            design_system=design_system,
            components_dir=components_dir,
            canvas=canvas,
        )
        if new_text != original:
            svg_file.write_text(new_text, encoding="utf-8")
            if verbose:
                safe_print(f"   [OK] {svg_file.name}: components/tokens applied")
            return True
        return False
    except Exception as e:
        safe_print(f"   [ERROR] {svg_file.name}: {e}")
        return False


def safe_print(text: str) -> None:
    """Print text while tolerating Windows terminal encoding limits."""
    try:
        print(text)
    except UnicodeEncodeError:
        replacements = {
            chr(0x23F3): "[..]",
            chr(0x2705): "[DONE]",
            chr(0x274C): "[ERROR]",
            chr(0x26A0) + chr(0xFE0F): "[WARN]",
            chr(0x1F4C1): "[DIR]",
            chr(0x1F4C4): "[FILE]",
            chr(0x1F4E6): "[OK]",
        }
        for source, target in replacements.items():
            text = text.replace(source, target)
        print(text)


def process_flatten_text(svg_file: Path, verbose: bool = False) -> bool:
    """Flatten text in a single SVG file (in-place modification)"""
    try:
        from svg_finalize.flatten_tspan import flatten_text_with_tspans
        from xml.etree import ElementTree as ET

        tree = ET.parse(str(svg_file))
        changed = flatten_text_with_tspans(tree)

        if changed:
            tree.write(str(svg_file), encoding='unicode', xml_declaration=False)
            if verbose:
                safe_print(f"   [OK] {svg_file.name}: text flattened")
        return changed
    except Exception as e:
        if verbose:
            safe_print(f"   [ERROR] {svg_file.name}: {e}")
        return False


def process_rounded_rect(svg_file: Path, verbose: bool = False) -> int:
    """Convert rounded rectangles in a single SVG file (in-place modification)"""
    try:
        from svg_finalize.svg_rect_to_path import process_svg

        with open(svg_file, 'r', encoding='utf-8') as f:
            content = f.read()

        processed, count = process_svg(content, verbose=False)

        if count > 0:
            with open(svg_file, 'w', encoding='utf-8') as f:
                f.write(processed)
            if verbose:
                safe_print(f"   [OK] {svg_file.name}: {count} rounded rectangle(s)")
        return count
    except Exception as e:
        if verbose:
            safe_print(f"   [ERROR] {svg_file.name}: {e}")
        return 0


def finalize_project(
    project_dir: Path,
    options: dict[str, bool],
    dry_run: bool = False,
    quiet: bool = False,
    compress: bool = False,
    max_dimension: int | None = None,
    design_md: str | None = None,
    canvas: str | None = None,
    slides_filter: list[str] | None = None,
) -> bool:
    """
    Finalize SVG files in the project

    Args:
        project_dir: Project directory path
        options: Processing options dictionary
        dry_run: Preview only, do not execute
        quiet: Quiet mode, reduce output
        compress: Compress images before embedding
        max_dimension: Downscale images exceeding this dimension
        design_md: Optional path to DESIGN.md for token resolution
        canvas: Optional canvas variant name (ppt169, ppt43, ...)
        slides_filter: When set, only process SVG files whose stem matches one
                        of these slide IDs (e.g. ["03_m27", "04_music"]).
    """
    svg_output = project_dir / 'svg_output'
    svg_final = project_dir / 'svg_final'
    icons_dir = Path(__file__).parent.parent / 'templates' / 'icons'
    components_dir = Path(__file__).parent.parent / 'templates' / 'components'

    # Resolve DESIGN.md and components dir.
    design_path = _resolve_design_md(project_dir, design_md)
    design_system = _load_design_system(design_path)

    # Check if svg_output exists
    if not svg_output.exists():
        safe_print(f"[ERROR] svg_output directory not found: {svg_output}")
        return False

    # Get list of SVG files
    svg_files = list(svg_output.glob('*.svg'))
    if not svg_files:
        safe_print(f"[ERROR] No SVG files in svg_output")
        return False

    if not quiet:
        print()
        safe_print(f"[DIR] Project: {project_dir.name}")
        safe_print(f"[FILE] {len(svg_files)} SVG file(s)")
        if design_path:
            safe_print(f"[OK] DESIGN.md: {design_path}")
        if slides_filter:
            safe_print(f"[OK] Slides filter: {', '.join(slides_filter)}")

    if dry_run:
        safe_print("[PREVIEW] Preview mode, no operations will be performed")
        return True

    # Step 1: Copy directory (or refresh subset when --slides used)
    if slides_filter and svg_final.exists():
        # Keep existing finalized slides; only refresh the filtered set from svg_output.
        for sid in slides_filter:
            for src in svg_output.glob(f"{sid}*.svg"):
                shutil.copy2(src, svg_final / src.name)
    else:
        if svg_final.exists():
            shutil.rmtree(svg_final)
        shutil.copytree(svg_output, svg_final)

    # Compute the set of files we'll iterate over.
    def iter_targets():
        for f in svg_final.glob('*.svg'):
            if slides_filter and not any(f.stem == sid or f.stem.startswith(sid + "_") or f.stem == sid for sid in slides_filter):
                continue
            yield f

    if not quiet:
        print()

    # Step 0: Embed components + resolve DESIGN.md tokens
    if options.get('embed_components') and (components_dir.exists() or design_system is not None):
        if not quiet:
            safe_print("[1/7] Embedding components and resolving tokens...")
        ct_count = 0
        for svg_file in iter_targets():
            if process_components_and_tokens_in_file(
                svg_file, design_system, components_dir, canvas=canvas, verbose=False
            ):
                ct_count += 1
        if not quiet:
            if ct_count > 0:
                safe_print(f"      {ct_count} file(s) updated")
            else:
                safe_print("      No components or tokens to resolve")

    # Step 2: Embed icons
    if options.get('embed_icons'):
        if not quiet:
            safe_print("[2/7] Embedding icons...")
        icons_count = 0
        for svg_file in iter_targets():
            count = embed_icons_in_file(svg_file, icons_dir, dry_run=False, verbose=False)
            icons_count += count
        if not quiet:
            if icons_count > 0:
                safe_print(f"      {icons_count} icon(s) embedded")
            else:
                safe_print("      No icons")

    # Step 3: Smart crop images (based on preserveAspectRatio="slice")
    if options.get('crop_images'):
        if not quiet:
            safe_print("[3/7] Smart cropping images...")
        crop_count = 0
        crop_errors = 0
        for svg_file in iter_targets():
            count, errors = crop_images_in_svg(str(svg_file), dry_run=False, verbose=False)
            crop_count += count
            crop_errors += errors
        if not quiet:
            if crop_count > 0:
                safe_print(f"      {crop_count} image(s) cropped")
            else:
                safe_print("      No cropping needed (no images with slice attribute)")

    # Step 4: Fix image aspect ratio (prevent stretching during PPT shape conversion)
    if options.get('fix_aspect'):
        if not quiet:
            safe_print("[4/7] Fixing image aspect ratios...")
        aspect_count = 0
        for svg_file in iter_targets():
            count = fix_image_aspect_in_svg(str(svg_file), dry_run=False, verbose=False)
            aspect_count += count
        if not quiet:
            if aspect_count > 0:
                safe_print(f"      {aspect_count} image(s) fixed")
            else:
                safe_print("      No images")

    # Step 5: Embed images
    if options.get('embed_images'):
        if not quiet:
            safe_print("[5/7] Embedding images...")
        images_count = 0
        for svg_file in iter_targets():
            count, _ = embed_images_in_svg(str(svg_file), dry_run=False,
                                           compress=compress,
                                           max_dimension=max_dimension)
            images_count += count
        if not quiet:
            if images_count > 0:
                safe_print(f"      {images_count} image(s) embedded")
            else:
                safe_print("      No images")

    # Step 6: Flatten text
    if options.get('flatten_text'):
        if not quiet:
            safe_print("[6/7] Flattening text...")
        flatten_count = 0
        for svg_file in iter_targets():
            if process_flatten_text(svg_file, verbose=False):
                flatten_count += 1
        if not quiet:
            if flatten_count > 0:
                safe_print(f"      {flatten_count} file(s) processed")
            else:
                safe_print("      No processing needed")

    # Step 7: Convert rounded rects to Path
    if options.get('fix_rounded'):
        if not quiet:
            safe_print("[7/7] Converting rounded rects to Path...")
        rounded_count = 0
        for svg_file in iter_targets():
            count = process_rounded_rect(svg_file, verbose=False)
            rounded_count += count
        if not quiet:
            if rounded_count > 0:
                safe_print(f"      {rounded_count} rounded rectangle(s) converted")
            else:
                safe_print("      No rounded rectangles")

    # Done
    if not quiet:
        print()
        safe_print("[OK] Done!")
        print()
        print("Next steps:")
        print(f"  python scripts/svg_to_pptx.py \"{project_dir}\" -s final")

    return True


def main() -> None:
    """Run the CLI entry point."""
    parser = argparse.ArgumentParser(
        description=t("cli.finalize_svg.description"),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s projects/my_project           # Execute all processing (default)
  %(prog)s projects/my_project --only embed-icons fix-rounded
  %(prog)s projects/my_project -q        # Quiet mode

Processing options (for --only):
  embed-icons   Embed icons
  crop-images   Smart crop images (based on preserveAspectRatio)
  fix-aspect    Fix image aspect ratio (prevent stretching during PPT shape conversion)
  embed-images  Embed images
  flatten-text  Flatten text
  fix-rounded   Convert rounded rects to Path
        '''
    )

    parser.add_argument('project_dir', type=Path, help=t("cli.finalize_svg.arg_project_dir"))
    parser.add_argument('--only', nargs='+', metavar='OPTION',
                        choices=['embed-components', 'embed-icons', 'crop-images', 'fix-aspect', 'embed-images', 'flatten-text', 'fix-rounded'],
                        help=t("cli.finalize_svg.arg_only"))
    parser.add_argument('--slides', metavar='ID',
                        help='Comma-separated slide IDs to process (e.g. 03_m27,04_music). '
                             'When omitted, every SVG in svg_output is processed.')
    parser.add_argument('--design', metavar='PATH', default=None,
                        help='Path to DESIGN.md for token resolution. Auto-detected from '
                             'project/design_system.md or project/.ppt-master/template.txt.')
    parser.add_argument('--canvas', metavar='NAME', default=None,
                        help='Canvas variant for DESIGN.md "Canvas Variants" lookup (ppt169, ppt43).')
    parser.add_argument('--dry-run', '-n', action='store_true',
                        help=t("cli.finalize_svg.arg_dry_run"))
    parser.add_argument('--quiet', '-q', action='store_true',
                        help=t("cli.finalize_svg.arg_quiet"))
    parser.add_argument('--compress', action='store_true',
                        help=t("cli.finalize_svg.arg_compress"))
    parser.add_argument('--max-dimension', type=int, default=None,
                        help=t("cli.finalize_svg.arg_max_dimension"))

    args = parser.parse_args()

    if not args.project_dir.exists():
        safe_print(f"[ERROR] Project directory does not exist: {args.project_dir}")
        sys.exit(1)

    # Determine processing options
    if args.only:
        # Execute only specified steps
        options = {
            'embed_components': 'embed-components' in args.only,
            'embed_icons': 'embed-icons' in args.only,
            'crop_images': 'crop-images' in args.only,
            'fix_aspect': 'fix-aspect' in args.only,
            'embed_images': 'embed-images' in args.only,
            'flatten_text': 'flatten-text' in args.only,
            'fix_rounded': 'fix-rounded' in args.only,
        }
    else:
        # Execute all by default
        options = {
            'embed_components': True,
            'embed_icons': True,
            'crop_images': True,
            'fix_aspect': True,
            'embed_images': True,
            'flatten_text': True,
            'fix_rounded': True,
        }

    slides_filter = None
    if args.slides:
        slides_filter = [s.strip() for s in args.slides.split(',') if s.strip()]

    success = finalize_project(args.project_dir, options, args.dry_run, args.quiet,
                               compress=args.compress,
                               max_dimension=args.max_dimension,
                               design_md=args.design,
                               canvas=args.canvas,
                               slides_filter=slides_filter)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
