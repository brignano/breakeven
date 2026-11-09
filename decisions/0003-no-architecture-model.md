# 0003: No architecture model for a desktop app

Status: accepted
Date: 2026-11-03
From: #17

## Context
The fleet standard asks every repo that deploys more than one moving part to
keep a driftwood model, `architecture.yaml`, with a rendered
`docs/architecture.md`. Breakeven is one Python file built into a desktop app
by GitHub Actions; nothing is deployed or runs as a service.

## Decision
Breakeven keeps no `architecture.yaml` and no `docs/architecture.md`.

## Consequences
No model to maintain or validate in CI. A single static product page doesn't
change this (the standard exempts a single static site). If Breakeven gains
more than one deployed part (a site with a backend, a service, a scheduled
job), that change adds the model and a new ADR supersedes this one.
