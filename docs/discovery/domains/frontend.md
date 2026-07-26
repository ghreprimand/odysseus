# Frontend

Features in this document are generated from [`../feature-catalog.json`](../feature-catalog.json), the canonical inventory.

## FRONTEND-001 — Single Page Application Shell & Client Router

- **Domain**: `frontend`
- **Status**: `verified`
- **Evidence Maturity**: `E0`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: not-required — No separate environment-dependent runtime validation was identified during this documentation pass.

### Purpose

Main HTML5 SPA shell, DOM lifecycle initializers, tab navigation, and deep-link route handlers.

### Evidence summary

- `static/index.html` — `index.html` — Main SPA entry point containing modal roots and CSS bundles.
- `app.py` — `serve_index` — Serves index.html with dynamically generated CSP nonces.

### Unknowns

- Stale browser static cache if asset hashing is omitted during deployment.

## FRONTEND-002 — Dynamic Theme, Color System & Custom Fonts

- **Domain**: `frontend`
- **Status**: `verified`
- **Evidence Maturity**: `E0`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: not-required — No separate environment-dependent runtime validation was identified during this documentation pass.

### Purpose

Supports dark/light themes, custom CSS variables, color picker controls, and user font uploads.

### Evidence summary

- `static/js/theme.js` — `applyTheme` — Applies custom HSL theme variables to DOM document root.
- `routes/font_routes.py` — `setup_font_routes` — Allows uploading and serving custom WOFF2 font files.

### Unknowns

- Flash of unstyled content (FOUC) on slow connections.

## FRONTEND-003 — Window Manager, Tile Layout & Modal Control System

- **Domain**: `frontend`
- **Status**: `verified`
- **Evidence Maturity**: `E0`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: not-required — No separate environment-dependent runtime validation was identified during this documentation pass.

### Purpose

Manages draggable tool windows, snapped multi-tile viewports, modal dialog Z-ordering, and ESC key stacks.

### Evidence summary

- `static/js/modalManager.js` — `ModalManager` — Controls modal open/close transitions and focus trapping.
- `static/js/tileManager.js` — `TileManager` — Handles viewport split-pane grid arrangements.

### Unknowns

- Overlap artifacts when opening many simultaneous tool floating windows.

## FRONTEND-004 — Global Keyboard Shortcuts & Accessibility Controls

- **Domain**: `frontend`
- **Status**: `verified`
- **Evidence Maturity**: `E0`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: not-required — No separate environment-dependent runtime validation was identified during this documentation pass.

### Purpose

Provides configurable hotkeys (Ctrl+K search, Esc close, Alt+1-9 tabs) and high-contrast accessibility options.

### Evidence summary

- `static/js/keyboard-shortcuts.js` — `initShortcuts` — Binds global keydown handlers for system shortcuts.
- `static/js/a11y.js` — `initA11y` — Applies ARIA roles and dyslexic font toggles.

### Unknowns

- Browser keybinding collisions with browser default hotkeys.

## FRONTEND-005 — Markdown, LaTeX & Code Block Streaming Renderer

- **Domain**: `frontend`
- **Status**: `verified`
- **Evidence Maturity**: `E0`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: not-required — No separate environment-dependent runtime validation was identified during this documentation pass.

### Purpose

Parses incoming SSE markdown streams, renders KaTeX math formulas, syntax-highlighted code, and interactive runners.

### Evidence summary

- `static/js/markdown.js` — `renderMarkdown` — Converts markdown prose to HTML nodes with syntax highlighting.
- `static/js/streamingSegmenter.js` — `Segmenter` — Parses un-closed markdown fences during live stream.

### Unknowns

- DOM thrashing if streaming segmenter updates UI too frequently.

## FRONTEND-006 — Interactive Tour & Guided Onboarding System

- **Domain**: `frontend`
- **Status**: `verified`
- **Evidence Maturity**: `E0`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: not-required — No separate environment-dependent runtime validation was identified during this documentation pass.

### Purpose

Presents interactive step-by-step feature tours and UI tooltip hints for new users.

### Evidence summary

- `static/js/tourHints.js` — `startTour` — Renders guided feature tour overlays over target UI elements.

### Unknowns

- Tour step misalignment if window is resized mid-tour.

## FRONTEND-007 — Background Effects Prototyping Sandbox

- **Domain**: `frontend`
- **Status**: `dead-code-candidate`
- **Evidence Maturity**: `E1`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: not-required — No separate environment-dependent runtime validation was identified during this documentation pass.

### Purpose

Standalone sandbox page for prototyping visual background animations, waves, and whirlpool effects.

### Evidence summary

- `app.py` — `serve_backgrounds` — Serves visual background sandbox HTML page route.
- `static/wave-variants.html` — `wave-variants.html` — Interactive background effect prototyping sandbox variant.

### Unknowns

- Route `/backgrounds` in app.py L918 attempts to serve `static/backgrounds.html` which is missing from disk; variant templates `wave-variants.html` and `whirlpool-variants.html` exist.
