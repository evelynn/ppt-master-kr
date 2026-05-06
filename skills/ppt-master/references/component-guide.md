# SVG Component Library (PPT Master)

> Reusable, parameterized SVG components that slide SVGs reference via
> `<use data-component="category/name" .../>`. Companion to
> `references/design-md-spec.md`. Files live under
> `templates/components/<category>/<name>.svg`.

## Why components

A 30-slide deck reuses the same 4–6 visual primitives — a coloured product
tile, a pill badge, a stepped number callout, a bottom footer stripe — over
and over. Hard-coding them in every slide makes:

- **Edits painful** — fix a card and you have to fix it 12 times.
- **Brand changes lossy** — the LLM might invent a slightly different version
  of the card on the next pass.
- **PPTX importer impossible** — there's nowhere to record what a "card" is.

By centralizing each primitive in `templates/components/`:

1. SVGs reference them with a single `<use>` element + `data-*` slots.
2. The post-processor scales the component to fit a target box and substitutes
   text slots from `data-<slot>` attributes.
3. Token resolution then turns `{colors.brand-1}` etc. into hex.

## Author a component

Each component file is a self-contained SVG document at
`templates/components/<category>/<name>.svg`:

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 480 400" data-component="product-cards/coral">
  <rect x="0" y="0" width="480" height="400"
        rx="{rounded.hero}" ry="{rounded.hero}"
        fill="{colors.brand-1}"/>
  <text x="32" y="92"
        font-family="{font.heading}"
        font-size="{typography.heading-xl.size}"
        font-weight="{typography.heading-xl.weight}"
        fill="{colors.ink-inverse}">{{text.title}}</text>
  <text x="32" y="148"
        font-family="{font.body}"
        font-size="{typography.heading-md.size}"
        fill="{colors.ink-inverse}" fill-opacity="0.92">{{text.subtitle}}</text>
</svg>
```

Rules:

- The root `<svg>` element MUST declare a `viewBox`. The width and height of
  the box become the component's intrinsic size.
- Use design tokens (`{colors.*}`, `{rounded.*}`, `{spacing.*}`,
  `{typography.<tok>.size}`, `{font.<role>}`) wherever possible. Raw hex is
  allowed but discouraged — the lint pass will flag it.
- Use `{{text.<slot>}}` placeholders for any text the consumer should fill in.
  Slot names are kebab-case lowercase (`title`, `subtitle`, `body1`, `body2`).
- Don't include `<style>`, `class`, `<symbol>`, or any of the banned features
  from `references/shared-standards.md`.
- Filters / gradients in component-local `<defs>` are NOT yet supported by the
  embedder. Keep components flat or rely on parent-slide filters.

## Reference a component from a slide

```xml
<use data-component="product-cards/coral"
     data-title="M2.7"
     data-subtitle="Foundation Model"
     data-footer="200B · +18%"
     x="80" y="120" width="480" height="400"
     fill="{colors.brand-1}"/>
```

- `data-component` is the path under `templates/components/` (no `.svg`).
- Each `data-<slot>` populates the `{{text.<slot>}}` placeholder of the same
  name. Missing slots resolve to empty string.
- `x`, `y`, `width`, `height` place and scale the component. Aspect ratio
  is NOT preserved — the embedder applies the requested width/height directly.
- Optional `fill` / `stroke` attributes on the `<use>` are forwarded to the
  outer `<g>` and apply when the component leaves them as `currentColor` (rare;
  most components define their fills explicitly).

## Register a new component

1. Drop the SVG under the appropriate category directory (or create a new one).
2. Add an entry to `templates/components/components_index.json`:

```json
"my-cat/my-card": {
  "category": "my-cat",
  "viewBox": "0 0 480 400",
  "defaultWidth": 480,
  "defaultHeight": 400,
  "slots": ["title", "subtitle"],
  "tokens": ["{colors.brand-1}", "{colors.ink-inverse}", "{rounded.hero}"]
}
```

3. Add a `### my-cat/my-card` entry under `## Components` in your template's
   `DESIGN.md`, listing slot names and intended tokens.
4. The editor UI will surface the new component automatically the next time
   `/api/components` is fetched.

## Test locally

```bash
# Validate the DESIGN.md the component is registered against
python3 scripts/design_tokens.py validate templates/layouts/<slug>/DESIGN.md

# Embed-and-resolve a slide that uses the component, write to test_demo/svg_final/
python3 scripts/finalize_svg.py /tmp/test_demo \
    --only embed-components \
    --design templates/layouts/<slug>/DESIGN.md
```

The `minimax_demo` template under `templates/layouts/minimax_demo/` is a
working end-to-end reference — copy its 4 slides as starting examples.
