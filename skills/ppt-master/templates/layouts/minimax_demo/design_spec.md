# MiniMax Demo - design_spec.md

> Project-level usage record. Pairs with `DESIGN.md` (the system) and the four
> reference SVGs in this directory. Strategist outputs imitate this file.

## I. Project Information

| Item | Value |
| ---- | ----- |
| **Project Name** | minimax_demo |
| **Canvas Format** | PPT 16:9 (0 0 1280 720) |
| **Page Count** | 4 |
| **Design Style** | Bold dual-identity AI brand |
| **Target Audience** | Internal product review |
| **Use Case** | Quarterly product showcase |

## II. Visual System

This deck uses `templates/layouts/minimax_demo/DESIGN.md`. Reference colors
exclusively via tokens (e.g. `{colors.brand-1}`); the post-processing pipeline
resolves them.

## III. Content Outline

### Slide 01 — Cover

- **Components**: `slide-frames/cover-band`
- **Slots**: title="MiniMax Quarterly", subtitle="제품군 개요와 분기 하이라이트", meta="2026 Q2 · Product Office"

### Slide 02 — TOC

- **Layout**: 3 numbered items vertical
- **Components**: `decorations/accent-bar`, `callouts/number-circle` ×3, `slide-frames/footer-stripe`

### Slide 03 — Product Showcase

- **Layout**: Two product tiles side by side
- **Components**: `product-cards/coral`, `badges/new`, `product-cards/blue`, `slide-frames/footer-stripe`

### Slide 04 — Ending

- **Layout**: Centered hero closer
- **Components**: `decorations/accent-bar`

## IV. Speaker Notes

Generate matching `.md` files under `notes/` for each slide.

## V. Technical Constraints

See `references/shared-standards.md` and `references/design-md-spec.md`.
