# Poker Helper

A desktop helper for Texas Hold'em. It starts with a pot odds calculator: enter the pot and the bet, plus your cards if you like, and it tells you whether calling pays.

## Download

Go to **Releases** on the right side of this page and download the latest version:

- **Windows:** `PokerHelper-windows.zip`. Unzip it, open the `Poker Helper` folder, and double-click `Poker Helper.exe`. Keep the `_internal` folder next to it; the app needs it.
- **Mac:** `PokerHelper-mac.zip`. Unzip it and drag `Poker Helper` into Applications.

You don't need to install Python or anything else.

**First launch:** the app isn't signed (signing costs money every year), so your computer will warn you the first time you open it.

- **Windows** shows "Windows protected your PC". Click **More info**, then **Run anyway**.
- **Mac** says the app "can't be opened". Open **System Settings → Privacy & Security**, scroll down, and click **Open Anyway**. On older macOS versions, right-click the app and choose **Open** instead.

You only have to do this once. The Mac build runs on Apple Silicon Macs (M1 and later).

## How to use it

| Input | Meaning |
|---|---|
| Pot | Type everything in the middle, **including the bet you're facing** |
| To call | Type what you would put in |
| Your cards | Optional. Click cards in the deck to fill your hand, then the flop, turn and river in order. The gold slot is filled next. Click a slot, or the card again, to take it back |
| Opponents | Use **−** and **+** to set how many players are still in the hand |
| Outs | Counted for you on the flop and turn (see below). Before that, or to override the count, use **−** and **+** or a preset: flush draw (9), open-ended straight draw (8), gutshot (4) |

The window opens at a size that fits your screen. Drag it bigger or smaller, or maximize it, and the cards and text scale with it. The results update as you go. There is no button to press. A big banner shows **CALL** (green) or **FOLD** (red), with a bar comparing your equity to the equity you need.

## What you get back

- **Your outs and the danger cards, highlighted**: on the flop and turn, the app tries every card that could come next. Cards that put you ahead turn **gold**, and cards that help but not enough turn **green**. Cards that help your opponents turn **red**: ones that leave you 10 points worse off than a typical next card, or 5 points when that turns a call into a fold (the third flush card, the card that fills a straight). Every card is measured against a typical next card, not against your chance right now, so a blank turn that just uses up one of your draws isn't flagged. Point at a card to see your chance to win if it comes, next to the chance after a typical card. The gold cards are your outs, and the app counts them for you.

- **Pot odds** and the **equity you need** to break even: call ÷ (pot + call).
- **Outs**: the exact chance of hitting on the next card and by the river.
- **Equity**: your chance to win at showdown. It runs 5,000 simulated hands against random opponent hands, and ties split the pot.
- **A verdict** (CALL or FOLD) and the EV of calling.

The verdict uses pot odds alone. It doesn't count implied odds (what you could win on later streets) or your read on the other players' ranges.

## For developers

The app is one Python file and uses only the standard library (Tkinter).

```
python3 pot_odds.py       # run it
pip install pytest && pytest -q   # run the tests
```

**Releasing:** in the Actions tab, open **build**, click **Run workflow**, and enter a version such as `v0.2.0`. You can also push a tag with that name. Either way, GitHub Actions runs the tests, builds the Windows and Mac apps with PyInstaller, and attaches both zips to a release. Every push to `main` also builds them, and you can download those builds from the Actions run.

## Code signing policy

The Windows app is being set up for free code signing through [SignPath Foundation](https://signpath.org). Until that is approved, releases are unsigned (see **First launch** above). Once approved: free code signing provided by [SignPath.io](https://signpath.io), certificate by [SignPath Foundation](https://signpath.org).

- **Committers and approvers:** [@brignano](https://github.com/brignano)
- Every release is built from this repository by GitHub Actions (`.github/workflows/build.yml`). Nothing built on a personal computer is signed.
- Each signing request is approved by hand by an approver.

**Privacy:** this program will not transfer any information to other networked systems unless specifically requested by the user or the person installing or operating it. It makes no network connections at all.

## License

[MIT](LICENSE)
