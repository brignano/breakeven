#!/bin/sh
# Assemble _site/ (what Cloudflare serves) from site/ and the shared assets.
# docs/images/ stays the only copy of the screenshots in git.
set -eu
cd "$(dirname "$0")/.."
rm -rf _site && mkdir -p _site/images
cp site/* _site/
cp docs/images/*.png _site/images/
cp assets/icon.png assets/icon.svg _site/
sed -i.bak "s/{{YEAR}}/$(date -u +%Y)/" _site/index.html && rm _site/index.html.bak
