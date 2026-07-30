# Design Reference: Revspot Token Extraction

- Document ID: DOC-UX-DESIGN-REF-REVSPOT
- Status: ACTIVE (reference material only — not an implementation task, not scheduled into any release)
- Version: 1.0
- Last updated: 2026-07-30
- Owner: Product owner (Ravi), captured by coding agent
- Related documents: [DESIGN_REFERENCES](DESIGN_REFERENCES.md), [PRD](../01-product/PRD.md), [FUTURE_SCOPE_LEAD_INTELLIGENCE](../01-product/FUTURE_SCOPE_LEAD_INTELLIGENCE.md)

## What this is

Real computed CSS values pulled directly from `revspot.ai`'s live stylesheet on
2026-07-30 (via `getComputedStyle()` in a real browser session — not estimated from
screenshots), plus a proposed way to fold the useful *structural* parts into Growixa's
own `globals.css`.

## Scope caveat — read before touching any CSS from this

Growixa's brand identity (navy `#0B1E3F`, blue `#1457E6`, teal `#12B8B0`, mint `#5EEAD4`,
success green `#22A06B`) is already approved by the product owner and already implemented
across the login screen, dashboard mockup, and shipped pages (see
[DESIGN_REFERENCES.md](DESIGN_REFERENCES.md)). Revspot's actual palette is a completely
different identity (warm cream/black/gold). **Nothing here proposes replacing Growixa's
colors.** What's worth adopting is Revspot's *token architecture* — how spacing, radius,
motion, and type are systematized — which is more mature than what `globals.css` has
today, independent of which hex values sit inside it.

## Raw extracted tokens (revspot.ai, captured 2026-07-30)

### Color tokens — light mode

| Token | Value | Use |
|---|---|---|
| `--paper` | `#FCFBF9` | page background |
| `--paper-2` | `#F6F5F1` | secondary surface |
| `--paper-3` | `#EFEEE8` | tertiary surface |
| `--hairline` | `#E7E5DE` | default border |
| `--hairline-2` | `#D9D6CD` | stronger border |
| `--ink` | `#121210` | primary text |
| `--ink-2` | `#37362F` | secondary text |
| `--ink-3` | `#75726A` | muted/caption text |
| `--agent` | `#4DA3FF` | AI/agent accent |
| `--agent-deep` | `#2F6FCC` | agent accent, text-safe variant |
| `--amber` | `#D6A24A` | highlight accent |
| `--amber-deep` | `#A87520` | amber, text-safe variant |
| `--green` | `#4FA37A` | success accent |
| `--green-deep` | `#37795A` | success, text-safe variant |

### Color tokens — dark mode

| Token | Value |
|---|---|
| `--d-bg` | `#101011` |
| `--d-bg-2` | `#161617` |
| `--d-bg-3` | `#1C1C1E` |
| `--d-line` | `#262628` |
| `--d-line-2` | `#323234` |
| `--d-ink` | `#F1F0EC` |
| `--d-ink-2` | `#A5A39C` |
| `--d-ink-3` | `#6E6C66` |
| `--d-agent` | `#6FB6FF` |
| `--d-amber` | `#E6BC74` |
| `--d-green` | `#6FBF97` |

**The pattern worth copying:** every accent ships as a pair — a light/tint value for
backgrounds and a "-deep" value for text on that tint, so a status chip's text always
passes contrast against its own low-opacity background. Growixa's current tokens don't
pair like this (`--color-success: #22a06b` has no "-deep" counterpart).

### Typography

- One typeface for everything: **Geist** (Vercel's open-source variable sans) — both
  display and body resolve to the same family.
- Uses **fractional/variable font weights** (380, 420, 450), not just 400/500/600/700 —
  a subtler optical-weight tuning only a variable font can do.
- Heading scale actually in use:

  | Level | Size | Weight | Line-height | Letter-spacing |
  |---|---|---|---|---|
  | H1 | 40px | 400 | 42.4px (1.06) | -1.76px |
  | H2 | 31px | 380 | 32.86px (1.06) | -1.178px |
  | H3 | 18px | 420 | 20.88px (1.16) | -0.432px |
  | micro-label | 11px | 600 | 17.05px | — |
  | pill/chip text | 8–9.5px | 550–650 | — | — |

- Letter-spacing tightens as size grows (~-4.4% of font-size at H1, ~-2.4% at H3) — the
  standard "tightened display type" technique that reads as more deliberate than default
  browser tracking.

### Radius scale

| Token | Value |
|---|---|
| `--r-sm` | 8px |
| `--r-md` | 12px |
| `--r-lg` | 16px |
| `--r-xl` | 20px |
| pill (chips/badges) | 999px |

Growixa currently has exactly two hardcoded radius values (`--card-radius: 18px`,
`--pill-radius: 14px`) with no scale between them.

### Motion

- `--ease: cubic-bezier(.22,1,.36,1)` — one reusable easing curve (fast start, soft
  settle) applied to every reveal/rise animation site-wide. Growixa has no motion tokens
  today.

### Spacing

- `--pad: clamp(20px, 4vw, 56px)` — a single fluid token used as horizontal page padding
  at every breakpoint, instead of separate fixed values per breakpoint.
- `--banner-h: 38px` — a named token just for the announcement-bar height, so other
  layout math can reference it instead of a magic number.

### Component recipes worth adapting (structure, not color)

**1. Status chip formula** (used for "Live/Learning/Scheduled", "Hot/Warm/Cold", etc.) —
one recipe, any accent color swapped in:

```
background: 9% opacity of the accent
border: 1px solid, 40% opacity of the accent
text: the accent's "-deep" variant
border-radius: 999px
padding: 2.5px 8px
font: 8px / weight 650
```

Growixa's status pills (Team page's Active/Disabled badge, campaign status in the
mockup) each use a one-off color today rather than one shared formula.

**2. Primary button "glossy dark" shadow recipe** — three stacked shadows on a flat
color, no gradient:

```
background: ink (near-black)
border: 1px solid rgba(ink, 0.92)
box-shadow:
  inset 0 1px 0 rgba(255,255,255,0.16),   /* top highlight */
  inset 0 -1px 0 rgba(0,0,0,0.42),        /* bottom shadow */
  0 10px 24px -14px rgba(ink,0.55);       /* ambient drop shadow */
border-radius: 12px
```

Growixa's spec calls for a *gradient* pill button (blue→teal), so this doesn't map 1:1 —
but layering an inset-highlight + inset-shadow + ambient-shadow on top of the existing
gradient fill would make it feel more three-dimensional without changing its color.

**3. Product-card hero background** — a radial gradient fading from a light center to a
warm edge (light cards) or a diagonal near-black gradient (dark cards), always full-bleed
behind the content, never a flat fill. Growixa's dashboard mockup already does this for
its one KPI hero card (navy/teal gradient, mint glow) — Revspot applies the same idea to
*every* product card, which is a reasonable extension once more cards exist.

## Proposed adoption for Growixa (architecture only, brand colors unchanged)

```css
:root {
  /* existing Growixa brand colors — unchanged */
  --color-primary-blue: #1457e6;
  --color-teal: #12b8b0;
  --color-mint: #5eead4;
  --color-success: #22a06b;
  --color-success-deep: #15754d; /* NEW — text-safe pair, Revspot pattern */
  --color-slate: #64748b;
  --color-slate-light: #94a3b8;
  --color-dark-text: #0b1b33;
  --color-nav-inactive: #9ca9c7;

  /* NEW — radius scale, replaces the two hardcoded one-offs */
  --r-sm: 8px;
  --r-md: 12px;
  --r-lg: 16px;
  --r-xl: 20px;
  --r-pill: 999px;

  /* NEW — motion */
  --ease: cubic-bezier(0.22, 1, 0.36, 1);

  /* NEW — fluid spacing */
  --pad: clamp(20px, 4vw, 56px);

  --gradient-primary: linear-gradient(135deg, var(--color-primary-blue), var(--color-teal));
  --gradient-sidebar: linear-gradient(150deg, #0b1e3f, #0a2a2c);
  --gradient-login-bg: linear-gradient(160deg, #0b1e3f 0%, #081428 55%, #052a2e 100%);
  --gradient-hero-card: linear-gradient(135deg, #0b1e3f, #0a3a3c);

  --card-radius: var(--r-lg); /* was a bare 18px; now traceable to the scale */
  --card-shadow: 0 4px 24px rgba(15, 42, 86, 0.07);
  --pill-radius: var(--r-pill); /* was a bare 14px; status pills read better fully round */

  --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}

.chip {
  display: inline-flex;
  align-items: center;
  border-radius: var(--r-pill);
  padding: 2.5px 8px;
  font-size: 8px;
  font-weight: 650;
  border: 1px solid color-mix(in srgb, var(--chip-color) 40%, transparent);
  background: color-mix(in srgb, var(--chip-color) 9%, transparent);
  color: var(--chip-color-deep);
}
.chip.c-success {
  --chip-color: var(--color-success);
  --chip-color-deep: var(--color-success-deep);
}
```

**Not applied to any live file yet.** This is a proposal to pick up as its own small
tracked task (would touch `globals.css` plus every component using the old bare radius
values and one-off status-pill colors) rather than folded silently into whatever feature
task next happens to touch those files — so it gets its own before/after verification
like every other tracked change in this project.

## Sources

- https://revspot.ai/ (homepage, product/module cards)
- https://revspot.ai/about.html
- https://revspot.ai/careers.html
- Values captured via `getComputedStyle()` / stylesheet inspection, 2026-07-30.
