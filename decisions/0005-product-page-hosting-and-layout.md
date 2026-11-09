# 0005: The product page is static HTML on a Worker, public on its hostname only

Status: accepted
Date: 2026-11-09
From: [proposals/product-page.md](../proposals/product-page.md), issue #24, PR #27

## Context
Breakeven needed a page for poker players at `breakeven.brignano.io`, not just
the GitHub README. Several things had to be settled. Where the page lives and
how it is built. How it reuses the screenshots without a second copy in git.
How it stays on the same design system release as the app. Which doors are
public. How to fit two downloads and an FAQ into the design system's
product-page layout, which allows one primary action and has no FAQ slot.

## Decision
- **Source and build.** Plain HTML and CSS live in `site/`. A small
  `scripts/build-site.sh` builds the gitignored `_site/`: it copies the
  `docs/images/*.png` and the icon, and stamps the year. That folder is what
  the Worker serves.
- **Styling.** `tokens.css` and `product-page.css` load from jsDelivr, pinned
  to `DESIGN_TOKENS`, with the `tier-marketing` tier. CI fails if the pin
  drifts from the app's, or if `site/` contains a literal colour.
- **Hosting.** A Cloudflare Worker with static assets (`breakeven`), deployed
  by Workers Builds with PR previews. There is no deploy workflow.
- **Access.** A hostname Access application with `Bypass` / `Everyone` for
  `breakeven.brignano.io` only, created before the domain is attached.
  `workers.dev` and previews stay on the `Me` floor.
- **Layout.** "Download" is the single primary action. It jumps to a panel
  with equal Windows and Mac buttons. The FAQ is the fourth story chapter.

## Consequences
The page costs $0 a month, and the screenshots have one source of truth.
Feature changes now touch two places: the README and `site/index.html` move
together. Bumping the design system is still one edit that CI forces through.
Setting it up needs Anthony in the Cloudflare dashboard (proposal, "What
Anthony does in Cloudflare"). A Worker-level bypass is ruled out, because it
would expose every preview.
