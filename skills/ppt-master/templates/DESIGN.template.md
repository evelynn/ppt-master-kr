# DESIGN.md (template)

> Copy this file to `templates/layouts/<slug>/DESIGN.md` and fill in the
> values. See `references/design-md-spec.md` for the full specification.
> Section headings are parsed verbatim — keep them in English and in this
> order. Field values may be in any language.

## Overview

[Brand voice, target audience, deck tone. Two or three sentences.]

## Colors

### Brand & Accent
| Token | Hex | Role | Usage |
| ----- | --- | ---- | ----- |
| primary | #111111 | Anchor | Hero backgrounds, primary text on light surfaces |
| brand-1 | #FF4E3A | Brand | Product card 1, CTAs |
| brand-2 | #2D7DFF | Brand | Product card 2 |
| accent  | #F5C518 | Accent | Highlights, callouts |

### Surface
| Token | Hex | Role |
| ----- | --- | ---- |
| canvas | #FFFFFF | Page background |
| surface-1 | #F5F5F5 | Card background |
| surface-2 | #E5E5E5 | Borders, dividers |

### Text
| Token | Hex | Role |
| ----- | --- | ---- |
| ink | #111111 | Primary body |
| ink-muted | #6B6B6B | Secondary |
| ink-inverse | #FFFFFF | On dark surfaces |

### Semantic
| Token | Hex | Role |
| ----- | --- | ---- |
| success | #16A34A | Positive markers |
| warning | #F97316 | Cautions |
| danger  | #DC2626 | Errors |

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
| heading-md   | 40 | 600 | 1.20 | 0       | Subtitles |
| body-lg      | 24 | 400 | 1.45 | 0       | Body 1x baseline |
| body-md      | 18 | 400 | 1.50 | 0       | Captions, dense |
| micro        | 12 | 500 | 1.40 | 0.04em  | Footers, page numbers |

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

## Elevation & Depth

| Token | Effect | SVG implementation |
| ----- | ------ | ------------------ |
| elevation.0 | Flat | (no filter) |
| elevation.1 | Subtle card lift | `filter="url(#shadow-1)"` |
| elevation.2 | Floating card | `filter="url(#shadow-2)"` |
| elevation.3 | Hero band drop | `filter="url(#shadow-3)"` |

### Filter defs
```svg
<filter id="shadow-1" x="-20%" y="-20%" width="140%" height="140%">
  <feDropShadow dx="0" dy="2" stdDeviation="6" flood-opacity="0.08"/>
</filter>
<filter id="shadow-2" x="-20%" y="-20%" width="140%" height="140%">
  <feDropShadow dx="0" dy="6" stdDeviation="14" flood-opacity="0.12"/>
</filter>
<filter id="shadow-3" x="-20%" y="-20%" width="140%" height="140%">
  <feDropShadow dx="0" dy="12" stdDeviation="24" flood-opacity="0.18"/>
</filter>
```

## Shapes

### Rounded corner scale
| Token | px |
| ----- | -- |
| xs   | 4 |
| sm   | 8 |
| md   | 12 |
| lg   | 16 |
| xl   | 24 |
| hero | 32 |
| full | 9999 |

### Borders
| Token | Width | Color |
| ----- | ----- | ----- |
| hairline | 1 | {colors.surface-2} |
| accent   | 2 | {colors.brand-1} |

## Components

### product-cards/coral
Tile-shaped product card with bold colored background, large title in the
top-left, subtitle below, and an optional badge in the top-right.

- **Background**: `{colors.brand-1}`
- **Text**: `{colors.ink-inverse}`
- **Rounded**: `{rounded.hero}`
- **Padding**: `{spacing.xl}`
- **Title typography**: `{typography.heading-xl}`
- **Subtitle typography**: `{typography.heading-md}`
- **Slots**: `data-title`, `data-subtitle`, `data-badge` (optional)
- **Default size**: 480 × 400

### badges/new
Pill-shaped highlight badge in accent color.

- **Background**: `{colors.accent}`
- **Text**: `{colors.ink}`
- **Rounded**: `{rounded.full}`
- **Slots**: `data-text`
- **Default size**: 80 × 32

## Slide Templates

### cover_dark
Black canvas with a brand-1 accent bar, hero-display title, and byline at the
bottom.

- **Slots**: `data-title`, `data-subtitle`, `data-meta`

### content_split_5_5
Two equal columns with a full-width title on top.

- **Slots**: `data-title`, `data-left`, `data-right`

## Do's and Don'ts

### Do
- Reference colors via `{colors.<token>}`, not raw hex.
- Use one type-size per role; respect the hierarchy.
- Embed components by `<use data-component="...">`; do not inline-copy a card.
- Keep cover slides to 1 hero-display + 1 subtitle + 1 byline maximum.

### Don't
- Don't use `class=` or `<style>` (banned by SVG constraints).
- Don't introduce a new color outside the palette.
- Don't mix more than 3 brand colors on one slide.
- Don't apply `<g opacity>` (banned by PPT compatibility).

## Canvas Variants

| Element | ppt169 | ppt43 | Notes |
| ------- | ------ | ----- | ----- |
| typography.hero-display.size | 96 | 80 | Smaller hero on 4:3 |
| spacing.xl | 32 | 24 | Tighter padding on 4:3 |

## Known Gaps

- [List anything the importer or designer could not fully resolve.]
