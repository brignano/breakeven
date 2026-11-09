# 0001: Releases stay unsigned for now

Status: accepted
Date: 2026-11-09
From: #22, and the SignPath outcome in commit 0a73bd6

## Context
Unsigned releases make Windows SmartScreen and macOS Gatekeeper warn on first
launch, the biggest drop-off between reading the README and using the app.
Free signing through SignPath Foundation was applied for and turned down.
The paid options on the table were:

- Windows: Azure Trusted Signing, about $10 a month, signing in CI.
- Mac: an Apple Developer Program account, $99 a year, for Developer ID
  signing plus notarization.
- Neither: $0, with first-launch instructions in the README.

## Decision
Neither for now. Releases stay unsigned and the README keeps its folded
first-launch instructions. Revisit when the downloads badge shows real use;
Mac signing comes first then, because Gatekeeper's block is harsher than
SmartScreen's warning.

## Consequences
No recurring cost and no signing secrets in CI. Every new user still has to
click through a warning once, so the README's "Your computer warns you"
block must stay accurate. Signing later means new secrets and `build.yml`
changes, both protected areas.
