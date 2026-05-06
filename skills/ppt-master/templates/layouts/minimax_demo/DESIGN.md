# MiniMax Demo — DESIGN.md

> Reference template demonstrating the DESIGN.md token system and the
> shared SVG component library. Inspired by the MiniMax brand palette.
> Use `templates/DESIGN.template.md` as a starting point for your own
> templates and replace section content; keep the section headings.

## Overview

A bold, dual-identity AI-product deck. Coral and electric blue product tiles
sit on a near-black canvas; type is set in DM Sans / Pretendard for crisp
Korean–Latin pairing. Aimed at product launches and quarterly reviews.

## Colors

### Brand & Accent
| Token | Hex | Role | Usage |
| ----- | --- | ---- | ----- |
| primary | #0B0B0F | Anchor | Cover and section backgrounds |
| brand-1 | #FF4E3A | Brand coral | Product card 1, hero accents |
| brand-2 | #2D7DFF | Brand blue | Product card 2 |
| accent  | #F5C518 | Accent | "NEW" badges, highlights |

### Surface
| Token | Hex | Role |
| ----- | --- | ---- |
| canvas | #FFFFFF | Page background (light pages) |
| surface-1 | #F4F4F6 | Card background |
| surface-2 | #E5E5EA | Borders, dividers |

### Text
| Token | Hex | Role |
| ----- | --- | ---- |
| ink | #111111 | Primary body |
| ink-muted | #6B6B73 | Secondary |
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
| heading-xl   | 72 | 700 | 1.10 | -0.01em | Section dividers, large product tile titles |
| heading-lg   | 48 | 700 | 1.15 | -0.01em | Slide titles |
| heading-md   | 32 | 600 | 1.20 | 0       | Subtitles |
| body-lg      | 22 | 400 | 1.45 | 0       | Body 1x baseline |
| body-md      | 18 | 400 | 1.50 | 0       | Captions |
| micro        | 12 | 500 | 1.40 | 0.04em  | Footer metadata |

## Layout

### Canvas
| Format | viewBox | Margins (T/R/B/L) | Grid columns | Gutter |
| ------ | ------- | ----------------- | ------------ | ------ |
| ppt169 | 0 0 1280 720 | 60 / 80 / 60 / 80 | 12 | 24 |
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

### Filter defs
```svg
<filter id="shadow-1" x="-20%" y="-20%" width="140%" height="140%">
  <feDropShadow dx="0" dy="2" stdDeviation="6" flood-opacity="0.08"/>
</filter>
<filter id="shadow-2" x="-20%" y="-20%" width="140%" height="140%">
  <feDropShadow dx="0" dy="6" stdDeviation="14" flood-opacity="0.12"/>
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
Bold colored product tile.
- **Background**: `{colors.brand-1}`
- **Text**: `{colors.ink-inverse}`
- **Rounded**: `{rounded.hero}`
- **Slots**: `data-title`, `data-subtitle`, `data-footer`
- **Default size**: 480 × 400

### product-cards/blue
Same shape as coral with brand-2 background.
- **Slots**: `data-title`, `data-subtitle`, `data-footer`
- **Default size**: 480 × 400

### cards/feature
Light card with a coloured top accent bar.
- **Slots**: `data-title`, `data-subtitle`, `data-body1`, `data-body2`, `data-body3`
- **Default size**: 360 × 280

### badges/new
Pill highlight badge in accent yellow.
- **Slots**: `data-text`
- **Default size**: 80 × 32

### callouts/number-circle
Numbered step indicator in brand coral.
- **Slots**: `data-number`
- **Default size**: 64 × 64

### slide-frames/cover-band
Full-canvas cover frame with hero title and bottom accent bar.
- **Slots**: `data-title`, `data-subtitle`, `data-meta`
- **Default size**: 1280 × 720

### slide-frames/footer-stripe
Slim bottom stripe with three text slots.
- **Slots**: `data-left`, `data-center`, `data-right`
- **Default size**: 1280 × 36

## Slide Templates

### cover_dark
Hero cover. Black canvas, brand-1 accent bar, hero-display title, byline.
- **Slots**: `data-title`, `data-subtitle`, `data-meta`

### product_showcase_2up
Two product tiles side by side, full-width title above.
- **Slots**: `data-title`, `data-card1.title`, `data-card1.subtitle`, `data-card2.title`, `data-card2.subtitle`

### content_steps_3
Three numbered step cards in a row.
- **Slots**: `data-title`, `data-step1`, `data-step2`, `data-step3`

### ending_thanks
Centered closer with accent decoration.
- **Slots**: `data-headline`, `data-meta`

## Do's and Don'ts

### Do
- Reference colors via `{colors.<token>}`, not raw hex.
- Use one type-size per role (cover = hero-display, slide = heading-lg).
- Embed product tiles via `<use data-component="product-cards/...">`.
- Keep cover slides to 1 hero-display + 1 subtitle + 1 byline.

### Don't
- Don't introduce a new color outside the palette.
- Don't use `<g opacity>` (banned by PPT compatibility).
- Don't mix coral and blue tiles on the same row in groups larger than 3.
- Don't apply `class=` or `<style>` (banned by SVG constraints).

## Canvas Variants

| Element | ppt169 | ppt43 | Notes |
| ------- | ------ | ----- | ----- |
| typography.hero-display.size | 96 | 80 | Smaller hero on 4:3 |
| spacing.xl | 32 | 24 | Tighter padding on 4:3 |

## Known Gaps

- SmartArt-style flow charts are not modeled; treat as raster fallback.
- Dark-mode of light pages not yet defined.
