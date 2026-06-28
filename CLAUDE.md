# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Static personal academic website for Harrison Nicholls, deployed via GitHub Pages to `nichollsh.github.io` and `www.h-nicholls.space` (set by `CNAME`). No build system, no dependencies — plain HTML and CSS.

## Previewing changes

Open any `.html` file directly in a browser, or serve locally:

```bash
python3 -m http.server 8080
```

## Structure

- `index.html` — landing page with research summary, links to publications, software, and contact
- `vitae.html` — full CV: employment, publications, teaching, awards, programming skills
- `internet.html` — curated list of external links
- `art.html` — art/photography landing page
- `res/sci.css` — stylesheet for science pages (`index.html`, `vitae.html`, `internet.html`); uses Outfit
- `res/art.css` — stylesheet for art pages (`art.html` and future art subpages); uses Libre Baskerville
- `res/fonts.css` — all `@font-face` declarations; imported by both stylesheets
- `res/fonts/` — self-hosted font TTFs: Inter (variable), Outfit (variable), Libre Baskerville (variable)
- `res/favicon.jpg`, `res/profile.jpg` — image assets
- `res/sci/thesis.pdf` — DPhil thesis (static asset)

## Conventions

**Fonts** — `res/fonts.css` is the single source for all `@font-face` declarations. Both `sci.css` and `art.css` import it with `@import url('fonts.css')`. To add a new font, add the TTFs under `res/fonts/` and add the `@font-face` block to `res/fonts.css` only.

**Responsive/print classes** (defined in the stylesheets):
- `.hide-on-small` — hidden on screens narrower than 600px; used for supplementary detail
- `.noprint` — hidden when printing; used for navigation links
- Print media query forces white background and black text

**Email obfuscation** — contact email addresses are split with HTML comments and a hidden `<span class="blockspam">` element to deter scraping bots. Preserve this pattern when editing contact information.

**Footer date** — all pages share the date via the CSS custom property `--page-updated` in each stylesheet's `:root` block. Each footer uses `<span class="page-updated-date"></span>` and the `.page-updated-date::after` rule injects the date via `content`. To update the date, change `--page-updated` in `sci.css` and `art.css`.

**No JavaScript** — do not add `<script>` tags or `.js` files. The site is pure HTML and CSS.

**Publications** — listed in reverse chronological order within `vitae.html`. Each entry uses `.tab1` for the title paragraph and `.tab2` for the detail paragraph (indented, negative top margin). Each paper has an `id` attribute used for anchor links (e.g. `id="paper_flares"`).

**Starfield background** — the dark space background in the stylesheets uses layered `radial-gradient` patterns at different `background-size` offsets to simulate a pseudo-random star field. Avoid simplifying or removing this.
