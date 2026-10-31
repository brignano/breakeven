# Breakeven

Know the price of every call. Breakeven is a desktop pot odds and equity calculator for Texas Hold'em: enter the pot and the bet, plus your cards if you like, and it tells you the equity you need to break even, the equity you have, and whether calling pays.

## Download

Go to **Releases** on the right side of this page and download the latest version:

- **Windows:** `Breakeven-windows.zip`. Unzip it and double-click `Breakeven.exe`.
- **Mac:** `Breakeven-mac.zip`. Unzip it and drag `Breakeven` into Applications.

Releases before the rename are called Poker Helper (`PokerHelper-*.zip`).

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
| Blinds | Small and big blind (1 / 2 to start). **+BB** and **−BB** under the pot and to call step them a big blind at a time, and the amounts are shown in big blinds too. **New hand** puts both blinds in the pot, sets to call to the big blind and clears the cards |
| Your cards | Optional. Click cards in the deck to fill your hand, then the flop, turn and river in order. The outlined blue slot is filled next. Click a slot, or the card again, to take it back |
| Opponents | Use **−** and **+** to set how many players are still in the hand |
| Outs | Counted for you on the flop and turn (see below). Before that, or to override the count, use **−** and **+** or a preset: flush draw (9), open-ended straight draw (8), gutshot (4) |

The window opens at a size that fits your screen. Drag it bigger or smaller, or maximize it, and the cards and text scale with it. The results update as you go. There is no button to press. A big banner shows **✓ CALL** (green) or **✕ FOLD** (red), with a bar comparing your equity to the tick that marks the equity you need.

It follows your system's light or dark mode. To pick one yourself, start it with `BREAKEVEN_THEME=light` or `BREAKEVEN_THEME=dark`.

## What you get back

- **Your outs and the danger cards, highlighted**: on the flop and turn, the app tries every card that could come next. Cards that put you ahead are filled green and marked **✓**, and cards that help but not enough get a green edge and a **+**. Cards that help your opponents are filled red and marked **▼**: ones that leave you 10 points worse off than a typical next card, or 5 points when that turns a call into a fold (the third flush card, the card that fills a straight). Every card is measured against a typical next card, not against your chance right now, so a blank turn that just uses up one of your draws isn't flagged. Point at a card to see your chance to win if it comes, next to the chance after a typical card. The ✓ cards are your outs, and the app counts them for you.

- **Pot odds** and the **equity you need** to break even: call ÷ (pot + call).
- **Outs**: the exact chance of hitting on the next card and by the river.
- **Equity**: your chance to win at showdown. It runs 5,000 simulated hands against random opponent hands, and ties split the pot.
- **A verdict** (CALL or FOLD) and the EV of calling.

The verdict uses pot odds alone. It doesn't count implied odds (what you could win on later streets) or your read on the other players' ranges.

## Review your PokerStars hands

After a session, see whether the calls and folds you made were priced right.

1. Click **Open hand history…**. It opens in the folder where PokerStars saves your hands:
   - **Windows:** `%LOCALAPPDATA%\PokerStars\HandHistory\<your name>`
   - **Mac:** `~/Library/Application Support/PokerStars/HandHistory/<your name>`

   PokerStars saves them by default. If the folder is empty, turn on **Settings → Playing History → Hand History** in PokerStars. You can pick several files at once.
2. Or copy a hand from PokerStars' hand replayer or a forum post, and click **Paste hand**.

A review window lists every spot where you faced a bet: the street, your cards and the board, the call and the pot, the equity you needed, your equity, and what you did. Each spot gets a price check:

| Check | Means |
|---|---|
| **✓ call paid** / **✓ good fold** | Your call had the price, or your fold didn't |
| **▲ called short** | Before the river you called without the price. The cards to come may still pay for it, so it's worth a look |
| **▲ fold had the price** | You folded with enough equity against random hands. Players who bet usually hold better than random hands, so it's worth a look, not a mistake |
| **✕ called short** | On the river you called without the price. Nothing is left to come, so this one cost you |

Select a row to load that spot into the calculator: the pot, the call, the blinds, the players left, your cards and the board. You get the full verdict, with outs and danger cards. Only Hold'em hands are read.

**Use it after you play, not during.** PokerStars and most other sites ban software that advises you while a hand is in progress (real-time assistance), and close accounts for it. Breakeven only reads hands that have finished, and only when you open them. Don't keep it open beside a real-money table.

## For developers

The app is one Python file and uses only the standard library (Tkinter).

```
python3 breakeven.py      # run it
pip install pytest && pytest -q   # run the tests
```

**Design system:** colours, type and the mark follow [brignano/design](https://github.com/brignano/design) (tool tier). `assets/tokens.css` is a copy of that repo's `tokens.css` at the release named by `DESIGN_TOKENS` in `.github/workflows/build.yml`, and CI fails if the two drift. The app reads every colour from that file, in light or dark, so `breakeven.py` holds no hex of its own (a test checks). To move to a newer release, replace the file, bump `DESIGN_TOKENS`, and regenerate the icon with `pip install pillow && python3 scripts/make_icon.py`.

**Releasing:** in the Actions tab, open **build**, click **Run workflow**, and enter a version such as `v0.2.0`. You can also push a tag with that name. Either way, GitHub Actions runs the tests, builds the Windows and Mac apps with PyInstaller, and attaches both zips to a release. Every push to `main` also builds them, and you can download those builds from the Actions run.

## Code signing

Releases are unsigned for now (see **First launch** above). Every release is built from this repository by GitHub Actions (`.github/workflows/build.yml`), so you can check exactly what went into it.

**Privacy:** this program will not transfer any information to other networked systems unless specifically requested by the user or the person installing or operating it. It makes no network connections at all.

## License

[MIT](LICENSE)
