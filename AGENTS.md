# Working on Breakeven

A desktop pot odds and equity calculator (`breakeven.py`, one file, standard library only) plus a product page for it (`site/`).

## Commands

- Tests: `pip install pytest && pytest -q`
- Product page, built and served locally: `sh scripts/build-site.sh && npx --yes serve _site`

## Keep docs and context in sync

- **README and the page say the same things.** A PR that changes a feature, the FAQ, the download names or the screenshots updates `README.md` and `site/index.html` together. The PR body lists both, or says why only one changed.
- **Screenshots live only in `docs/images/`.** `scripts/build-site.sh` copies them into the gitignored `_site/`. Never add a copy under `site/`.
- **Design tokens.** `DESIGN_TOKENS` in `.github/workflows/build.yml` names the `brignano/design` release. Bumping it also means replacing `assets/tokens.css` and changing the two `<link>`s (and `404.html`) in `site/`. CI checks both. No literal colours in `site/` either.
- Proposals and decisions: see `proposals/README.md` and `decisions/README.md`. Product page design: `proposals/product-page.md`, ADR 0005.

## Product page hosting

- A Cloudflare Worker `breakeven` serves `_site/` as static assets (`wrangler.jsonc`), deployed by Workers Builds. There is no deploy workflow here.
- `breakeven.brignano.io` is public through a **hostname** Access application (Bypass / Everyone). `workers.dev` and PR previews stay behind the account-wide `Me` floor.
- **Never add a Worker-level bypass.** It would open every preview too.
- The Cloudflare dashboard steps are in `proposals/product-page.md`. Cloud sessions can't do them.
