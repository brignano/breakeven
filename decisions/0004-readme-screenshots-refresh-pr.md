# 0004: CI regenerates the README screenshots and opens a refresh PR

Status: accepted
Date: 2026-11-09
From: [proposals/readme-screenshots-in-ci.md](../proposals/readme-screenshots-in-ci.md), issue #21

## Context
The README screenshots were captured once by hand and go stale with the next
UI change. A script can drive the app under Xvfb and regenerate them, but
font rendering shifts slightly between runner images, so CI can't expect
identical pixels. The options were: auto-commit new images onto the PR
branch, fail the PR when images drift, or open a separate refresh PR after
merge.

## Decision
A `screenshots` job regenerates the images and compares them with a fuzz
threshold. On a PR it only reports, never fails. After a merge to `main`, if
an image changed beyond the threshold, it opens or updates one "Refresh
README screenshots" PR for Anthony to merge. The calculator image shows
K♠K♦ on T♥9♥4♣, two opponents, 30 into 60, so outs, helpers and danger
cards all appear.

## Consequences
Feature PRs stay green whatever the runner's fonts do, and nothing is pushed
to `main` or onto someone's branch by a bot. A UI change is followed by one
extra PR to merge. The repo needs "Allow GitHub Actions to create pull
requests" turned on, and the job needs `pull-requests: write`. CI doesn't run
on the refresh PR (it is opened with the workflow token), which is acceptable
because it only changes PNGs. The build waits for #23 so the danger cards
are stable.
