# DESIGN.md Specification (PPT Master)

> Adapted from the `@google/design.md` format for slide-deck design systems.
> A `DESIGN.md` lives next to each layout template at
> `templates/layouts/<slug>/DESIGN.md` and acts as the **single source of truth**
> for color, typography, spacing, shape, elevation, components, and slide
> templates. SVG output references this system through `{token}` placeholders;
> the post-processing pipeline resolves them at finalize time.

## Why a token system

A PPT deck typically reuses the same six colors, four type sizes, three card
styles, and one rounded-corner radius across 10–40 slides. Hard-coding hex
values into every SVG makes:

- **Theme swaps** (rebrand, dark mode) painful — every slide must be edited.
- **Importing a sample PPT** lossy — there is no canonical place to record what
  the brand colors are, only their effects.
- **Consistency checks** impossible — "is `#ff5733` actually the brand color or
  did the LLM hallucinate a near-match?" cannot be answered.

By centralizing tokens in `DESIGN.md` and asking the Executor to write
`fill="{colors.brand-coral}"` instead of `fill="#FF4E3A"`:

1. Theme swaps are a one-line edit in `DESIGN.md`.
2. PPTX → DESIGN.md import has a clear extraction target.
3. Token reference checks (no orphan hex codes) become a lint pass.
4. Editor UI can expose a color picker that updates one token and re-renders
   the full deck instantly without an LLM call.

## File location and lifecycle

```
templates/
  layouts/
    <slug>/
      DESIGN.md          ← design system (this spec)
      design_spec.md     ← project-level usage (which slides use what)
      01_cover.svg       ← reference SVG slides
      02_toc.svg
      02_chapter.svg
      03_content.svg
      04_ending.svg
  components/            ← shared SVG component library (refer by name)
    components_index.json
    product-cards/
    cards/
    badges/
    decorations/
    callouts/
    slide-frames/
```

Every `DESIGN.md` MUST contain the following top-level sections, in this order:

1. Overview
2. Colors
3. Typography
4. Layout
5. Elevation & Depth
6. Shapes
7. Components
8. Slide Templates
9. Do's and Don'ts
10. Canvas Variants
11. Known Gaps

A starter `DESIGN.template.md` lives in `templates/`; copy and fill it in.

## Token reference syntax

Tokens are referenced inside SVG attribute values and inside other DESIGN.md
fields with curly braces:

| Token shape | Resolves to |
| ----------- | ----------- |
| `{colors.<name>}` | hex, e.g. `#FF4E3A` |
| `{typography.<name>}` | font size in **px** for SVG (parser also exposes `pt`, `weight`, `line_height`) |
| `{spacing.<name>}` | px, e.g. `32` |
| `{rounded.<name>}` | px, e.g. `16` |
| `{elevation.<name>}` | SVG `filter="url(#shadow-2)"` reference |
| `{font.heading}` / `{font.body}` / `{font.code}` | font-family stack |

### Component reference

Components are embedded with the existing `<use>` pattern (matches the icon
embedding convention). The post-processor substitutes the `<use>` element with
the component's full SVG group, scaled and positioned to the requested box,
with its internal tokens resolved.

```xml
<use data-component="product-cards/coral"
     data-title="M2.7"
     data-subtitle="Foundation Model"
     x="80" y="120" width="480" height="400"
     fill="{colors.brand-coral}"/>
```

Reserved attributes:

- `data-component="<category>/<name>"` — required, identifies the component.
- `data-<param>="..."` — text slot or override (component declares its slots in
  `components_index.json`).
- `x`, `y`, `width`, `height` — required, in canvas viewBox px.
- `fill`, `stroke` — optional overrides; if omitted, the component's defaults
  from `DESIGN.md` apply.

### Slide template reference

Macro-level templates (cover, section, content, ending) are referenced the
same way:

```xml
<use data-slide-template="content_split_5_5" .../>
```

Slide templates are typically used by the editor when adding a new slide; the
Executor more commonly writes raw SVG with embedded components.

## Section requirements

### 1. Overview

Free-form prose. Describe the **brand identity, deck tone, audience, and any
dual-identity considerations**. No tokens are defined here.

### 2. Colors

```markdown
## Colors

### Brand & Accent
| Token | Hex | Role | Usage |
| ----- | --- | ---- | ----- |
| primary | #111111 | Anchor | Hero backgrounds, primary text on light surfaces |
| brand-coral | #FF4E3A | Brand 1 | Product card 1, CTAs |
| ...

### Surface
| Token | Hex | Role |
| ----- | --- | ---- |
| canvas | #FFFFFF | Page background |
| surface-1 | #F5F5F5 | Card background |

### Text
| Token | Hex | Role |
| ----- | --- | ---- |
| ink | #111111 | Primary body |
| ink-muted | #6B6B6B | Secondary |

### Semantic
| Token | Hex | Role |
| ----- | --- | ---- |
| success | #16A34A | Positive markers |
| warning | #DC2626 | Issue markers |
```

The parser collects every row across all four sub-tables into a single
`colors` namespace. Token names must be `kebab-case` and unique across
sub-tables.

### 3. Typography

```markdown
## Typography

**Heading family**: "DM Sans", "Pretendard", -apple-system, sans-serif
**Body family**: "Inter", "Pretendard", -apple-system, sans-serif
**Code family**: "JetBrains Mono", Consolas, monospace

### Hierarchy
| Token | Size (px) | Weight | Line height | Letter spacing | Use |
| ----- | --------- | ------ | ----------- | -------------- | --- |
| hero-display | 96 | 700 | 1.05 | -0.02em | Cover only |
| heading-xl   | 72 | 700 | 1.10 | -0.01em | Section dividers |
| heading-lg   | 56 | 700 | 1.15 | -0.01em | Slide titles |
| heading-md   | 40 | 600 | 1.20 | 0    | Subtitles |
| body-lg      | 24 | 400 | 1.45 | 0    | Body 1x baseline |
| body-md      | 18 | 400 | 1.50 | 0    | Captions, dense |
| micro        | 12 | 500 | 1.40 | 0.04em | Footers, page numbers |
```

The parser exposes resolved typography as both `px` (for SVG) and `pt`
(`px / 1.333` rounded). Use `{typography.heading-lg.size}` for the px number,
`{typography.heading-lg.pt}` for the pt number, `{typography.heading-lg.weight}`
for the weight.

### 4. Layout

```markdown
## Layout

### Canvas
| Format | viewBox | Margins (T/R/B/L) | Grid columns | Gutter |
| ------ | ------- | ----------------- | ------------ | ------ |
| ppt169 | 0 0 1280 720 | 50 / 60 / 50 / 60 | 12 | 24 |
| ppt43  | 0 0 1024 768 | 60 / 60 / 60 / 60 | 12 | 24 |

### Spacing scale
| Token | px |
| ----- | -- |
| xxs | 4 |
| xs  | 8 |
| sm  | 12 |
| md  | 16 |
| lg  | 24 |
| xl  | 32 |
| xxl | 48 |
| 3xl | 64 |
| 4xl | 96 |
```

### 5. Elevation & Depth

```markdown
## Elevation & Depth

| Token | Effect | SVG implementation |
| ----- | ------ | ------------------ |
| elevation.0 | Flat | (no filter, optional 1px stroke) |
| elevation.1 | Subtle card lift | `filter="url(#shadow-1)"` |
| elevation.2 | Floating card | `filter="url(#shadow-2)"` |
| elevation.3 | Hero band drop | `filter="url(#shadow-3)"` |

### Filter defs (paste into each slide's `<defs>`)
```svg
<filter id="shadow-1" x="-20%" y="-20%" width="140%" height="140%">
  <feDropShadow dx="0" dy="2" stdDeviation="6" flood-opacity="0.08"/>
</filter>
```

The parser collects the `<filter>` defs and the embedder injects the requested
ones into each finalized slide's `<defs>` block on first use.

### 6. Shapes

```markdown
## Shapes

### Rounded corner scale
| Token | px |
| ----- | -- |
| xs  | 4  |
| sm  | 8  |
| md  | 12 |
| lg  | 16 |
| xl  | 24 |
| hero | 32 |
| full | 9999 |

### Borders
| Token | Width | Color |
| ----- | ----- | ----- |
| hairline | 1 | {colors.surface-2} |
| accent   | 2 | {colors.brand-coral} |
```

### 7. Components

```markdown
## Components

### product-cards/coral
Tile-shaped product card with bold colored background, large numeric/title in
the top-left, subtitle below, and an optional badge in the top-right.

- **Background**: `{colors.brand-coral}`
- **Text**: `{colors.canvas}` (white on coral)
- **Rounded**: `{rounded.hero}`
- **Padding**: `{spacing.xl}`
- **Title typography**: `{typography.heading-xl}`
- **Subtitle typography**: `{typography.heading-md}`
- **Slots**: `data-title`, `data-subtitle`, `data-badge` (optional)
- **Default size**: 480 × 400

### badges/new
Pill-shaped highlight badge.
- ...
```

Each component MUST also have a corresponding SVG file at
`templates/components/<category>/<name>.svg` whose attributes use the same
tokens the spec section names. The `components_index.json` is generated from
these files; see `references/component-guide.md`.

### 8. Slide Templates

```markdown
## Slide Templates

### cover_dark
- Black canvas, brand color accent bar, hero-display title, byline.
- Components: `slide-frames/cover-band`, `decorations/accent-bar`
- Slots: `data-title`, `data-subtitle`, `data-meta`

### content_split_5_5
- Two equal columns. Title on top spanning full width.
- Slots: `data-title`, `data-left`, `data-right`
```

### 9. Do's and Don'ts

```markdown
## Do's and Don'ts

### Do
- Reference colors via `{colors.<token>}`, not hex codes.
- Use one type-size per role (no ad-hoc sizes between hierarchy steps).
- Embed components by `<use data-component="...">`; do not inline copy a card.
- Keep cover slides to 1 hero-display + 1 subtitle + 1 byline maximum.

### Don't
- Don't use `class=` or `<style>` (banned by SVG constraints).
- Don't introduce a new color outside the palette.
- Don't mix more than 3 brand colors on one slide.
- Don't apply `<g opacity>` (banned by PPT compatibility).
```

Executor guides include this section verbatim as a guardrail.

### 10. Canvas Variants

PPT does not reflow. Define how key dimensions scale across canvas formats:

```markdown
## Canvas Variants

| Element | ppt169 | ppt43 | Notes |
| ------- | ------ | ----- | ----- |
| Cover hero size | 96px | 80px | Same token, scaled by canvas |
| Card padding | {spacing.xl} | {spacing.lg} | Tighter on 4:3 |
| Margin T/B | 50 | 60 | |
```

The parser exposes a `canvas_variant("ppt43", "spacing.xl") -> 24` lookup; the
embedder substitutes per the active canvas.

### 11. Known Gaps

Free-form list. The PPTX importer auto-records anything it could not extract
here. Strategist and Executor should treat these as out-of-scope for the
template.

## Validation

`python3 scripts/design_tokens.py validate <DESIGN.md>` checks:

- All 11 sections present.
- Color tokens are unique kebab-case.
- Typography tokens reference valid weight (100..900) and have positive size.
- Component sub-section names map to files in `templates/components/<...>.svg`.
- All `{token}` references inside the doc resolve.

`python3 scripts/design_tokens.py lint-svg <slide.svg> --design <DESIGN.md>`
checks that every hex color in the slide has a corresponding palette token
(unless the SVG has `<!-- design-md:freehex -->` opt-out).

## Korean (한국어) note

When PPT Master is in Korean mode, this spec's section headings remain in
English (so the parser can find them), but field values and prose can be in
Korean. The Korean overlay reference at `references/ko/design-md-spec.md`
contains a Korean-language explanation of the spec.
