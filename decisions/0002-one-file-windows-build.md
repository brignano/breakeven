# 0002: The Windows build is a single exe, not a folder

Status: accepted
Date: 2026-10-12
From: commits e77f492 and 43d8d96 (its revert)

## Context
A one-file PyInstaller exe unpacks itself into a temp folder at launch, which
antivirus tools often flag. Building with `--onedir` was tried to cut those
false positives: the Windows zip held the app folder instead of a single exe.
It didn't stop Windows warning users, and it made them dig through a folder
to find the exe.

## Decision
Build with `--onefile`, so the Windows zip holds just `Breakeven.exe`. Code
signing, not the PyInstaller layout, is what would clear the warning
(see [0001](0001-releases-stay-unsigned.md)).

## Consequences
Users unzip and double-click one file. Occasional antivirus false positives
remain possible until releases are signed. Don't switch to `--onedir` again
for the warning alone.
