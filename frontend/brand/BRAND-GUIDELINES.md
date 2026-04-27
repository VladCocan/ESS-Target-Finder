# ESS Target Finder — Brand Guidelines
Version 1.0.0

---

## 1. Logo

### Primary Mark
The ESS Target Finder mark consists of two elements:
- **Icon**: A military-grade crosshair with double rings, center dot, axis lines, and corner brackets
- **Wordmark**: "ESS" in Orbitron Black + "TARGET FINDER" in Orbitron Bold

### Variants
| File | Use Case |
|---|---|
| `logo-dark.svg` | Default — on dark/black backgrounds |
| `logo-light.svg` | Inverted — on light grey/white backgrounds |
| `logo-transparent.svg` | Overlay usage on images/video |
| `icon-mark.svg` | Standalone icon — app icons, small spaces |

### Minimum Size
- Full logo: min 160px wide
- Icon mark: min 24px × 24px

### Clear Space
Always maintain a clear zone equal to the height of the letter "E" around all sides of the logo.

### Do Not
- Rotate or skew the logo
- Change the color of individual elements
- Use the light-text version on a dark background
- Apply drop shadows or filters
- Stretch or distort proportions

---

## 2. Color Palette

### Primary
| Name | Hex | Usage |
|---|---|---|
| Cyan Prime | `#00B4FF` | Primary accent, CTAs, active states, icon |
| Cyan Light | `#33C6FF` | Hover states, highlights |
| Cyan Deep | `#0070A8` | Borders on light backgrounds |

### Semantic Status
| Name | Hex | Usage |
|---|---|---|
| Alert Red | `#FF3D5A` | High-risk targets, danger states |
| Amber Warn | `#FFAA00` | Medium risk, warnings |
| Intel Green | `#3A8C6A` | Success, null-sec confirmed, safe |

### Backgrounds
| Name | Hex | Usage |
|---|---|---|
| Void Black | `#06090F` | Page background, deepest surface |
| Deep Space | `#080C12` | Main content areas |
| Panel | `#0D1520` | Cards, sidebars, panels |
| Elevated | `#111B28` | Hover states, active elements |

### Text
| Name | Hex | Usage |
|---|---|---|
| Text Primary | `#E0EAF4` | Headlines, important values |
| Text Secondary | `#8AA0B4` | Body text, descriptions |
| Text Muted | `#3A5C7A` | Labels, secondary info |
| Text Faint | `#1E3248` | Decorative labels, micro-copy |

---

## 3. Typography

### Font Stack

**Display — Orbitron** (Google Fonts)
- Used for: headings, system names, scores, CTAs, logo wordmark
- Weights: 900 (Black) for H1/logo, 700 (Bold) for H2/H3
- Letter spacing: +0.08em to +0.35em depending on size

**Monospace — Share Tech Mono** (Google Fonts)
- Used for: code, API paths, coordinates, labels, badges, meta info
- Weight: 400 only
- Letter spacing: +0.1em to +0.35em

**Body — Rajdhani** (Google Fonts)
- Used for: body text, descriptions, UI labels
- Weights: 400 (regular), 600 (semi-bold)
- Line height: 1.6–1.7

### Import (HTML)
```html
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Share+Tech+Mono&family=Rajdhani:wght@300;400;600&display=swap" rel="stylesheet"/>
```

### Import (CSS)
```css
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Share+Tech+Mono&family=Rajdhani:wght@300;400;600&display=swap');
```

### Type Scale
| Token | Size | Font | Weight | Usage |
|---|---|---|---|---|
| H1 | 36px | Orbitron | 900 | Hero titles |
| H2 | 24px | Orbitron | 700 | Section headings |
| H3 | 18px | Orbitron | 700 | Card titles |
| Body | 15px | Rajdhani | 400 | Descriptions |
| Mono | 13px | Share Tech Mono | 400 | Code, coords |
| Label | 9–11px | Share Tech Mono | 400 | Badges, meta |

---

## 4. Favicon & App Icons

### Files
| File | Size | Format | Usage |
|---|---|---|---|
| `favicon-16.svg` | 16×16 | SVG | Browser tab (small) |
| `favicon-32.svg` | 32×32 | SVG | Browser tab (standard) |
| `favicon-64.svg` | 64×64 | SVG | High-DPI displays |
| `apple-touch-icon.svg` | 180×180 | SVG | iOS home screen |

### HTML Head Implementation
```html
<link rel="icon" type="image/svg+xml" href="/favicons/favicon-32.svg"/>
<link rel="apple-touch-icon" href="/favicons/apple-touch-icon.svg"/>
```

### Notes
- SVG favicons are supported in all modern browsers
- For legacy browser support, generate a `.ico` from `favicon-64.svg` using a converter
- The 16px variant uses a simplified crosshair (no corner brackets, no inner ring) for legibility at small sizes

---

## 5. Social / OG Image

**File**: `og-social-preview.svg`
**Dimensions**: 1200 × 630px (standard OG ratio)

```html
<meta property="og:image" content="/svg/og-social-preview.svg"/>
<meta property="og:image:width" content="1200"/>
<meta property="og:image:height" content="630"/>
<meta name="twitter:card" content="summary_large_image"/>
```

---

## 6. Design Principles

### Aesthetic Direction
**Dark Tactical / Sci-Fi Military**
Inspired by EVE Online's austere UI, military HUD systems, and signal intelligence tools. Every element should feel like it belongs in a command center, not a consumer app.

### Principles
1. **Dark first** — the app lives in space. Light backgrounds are only for print.
2. **Precision over decoration** — every pixel serves a purpose.
3. **Data is the hero** — the system name and score are always the most prominent elements.
4. **Color encodes meaning** — red = high risk, amber = medium, green = safe. Never use these colors decoratively.
5. **Monospace for data** — all coordinates, scores, system names, API endpoints use Share Tech Mono.

### Tone
- Direct and technical
- No marketing fluff
- System labels use ALL-CAPS + monospace
- Section labels prefixed with `//` (code comment style)

---

## 7. CSS Usage

Import `tokens.css` as the first stylesheet:
```html
<link rel="stylesheet" href="/css/tokens.css"/>
```

Key CSS variables:
```css
/* Colors */
var(--cyan-prime)     /* #00B4FF — main accent */
var(--alert-red)      /* #FF3D5A — high risk */
var(--amber-warn)     /* #FFAA00 — medium risk */
var(--intel-green)    /* #3A8C6A — safe/ok */
var(--bg-void)        /* #06090F — page bg */

/* Fonts */
var(--font-display)   /* Orbitron */
var(--font-mono)      /* Share Tech Mono */
var(--font-body)      /* Rajdhani */
```

---

## 8. File Structure

```
ess-brand/
├── svg/
│   ├── logo-dark.svg          ← Main logo (dark bg)
│   ├── logo-light.svg         ← Inverted logo (light bg)
│   ├── logo-transparent.svg   ← No background
│   ├── icon-mark.svg          ← Standalone icon
│   └── og-social-preview.svg  ← 1200×630 OG image
├── favicons/
│   ├── favicon-16.svg
│   ├── favicon-32.svg
│   ├── favicon-64.svg
│   └── apple-touch-icon.svg
├── css/
│   └── tokens.css             ← All design tokens + components
└── docs/
    └── index.html             ← Full UI demo / reference page
```
