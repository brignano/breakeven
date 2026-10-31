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

## Track and review your PokerStars hands

Start Breakeven and it keeps track for you. PokerStars saves each hand to a text file a few seconds after the hand ends, and Breakeven picks those files up every few seconds from where PokerStars keeps them:

- **Windows:** `%LOCALAPPDATA%\PokerStars\HandHistory\<your name>`
- **Mac:** `~/Library/Application Support/PokerStars/HandHistory/<your name>`

The line under the title shows what it has: *Tracking PokerStars · 42 hands this session · 3,180 in your history*. Hands from the 12 hours before you opened the app count as this session too, so you can play first and open Breakeven afterwards. If it says the folder wasn't found, turn on **Settings → Playing History → Hand History** in PokerStars. To use a different folder, start Breakeven with `BREAKEVEN_HAND_HISTORY=/path/to/folder`.

Click **Review session** to see the session's hands. You can also use **Open file…** for any hand history file, or copy a hand from PokerStars and click **Paste hand**.

### Your spots

Every spot where you faced a bet: the street, your cards and the board, the call and the pot, the equity you needed, your equity, and what you did. Each spot gets a price check:

| Check | Means |
|---|---|
| **✓ call paid** / **✓ good fold** | Your call had the price, or your fold didn't |
| **▲ called short** | Before the river you called without the price. The cards to come may still pay for it, so it's worth a look |
| **▲ fold had the price** | You folded with enough equity against random hands. Players who bet usually hold better than random hands, so it's worth a look, not a mistake |
| **✕ called short** | On the river you called without the price. Nothing is left to come, so this one cost you |

Select a row to load that spot into the calculator: the pot, the call, the blinds, the players left, your cards and the board.

### Players

Everyone you played with this session, read from every hand of theirs in your history:

| Column | Means |
|---|---|
| **Plays** | Share of hands they put money in by choice. Posting a blind doesn't count |
| **Raises** | Share of hands they raised before the flop |
| **Aggression** | Bets and raises per call after the flop. Above 1.5 counts as aggressive |
| **Style** | Tight or loose (playing at least 28% of hands is loose), and passive or aggressive, with what that usually means for you |

Under 20 hands, the numbers are mostly noise, so the player is greyed out and marked *Not enough hands*. Only hands you were dealt into are counted, and nothing leaves your computer.

Only Hold'em hands are read.

### Playing by the rules

Breakeven reads only finished hands from the files PokerStars itself writes. It never reads the PokerStars window, its memory, or its logs, and it never looks at a hand while it's being played.

Poker sites ban software that advises you during a hand (real-time assistance), and they close accounts for it. Trackers that build player stats from your own hand histories are a long-standing, accepted category, but PokerStars keeps its own list of approved tools, and Breakeven isn't on it. Before you keep Breakeven open beside a real-money table, check PokerStars' current rules on third-party tools. If in doubt, review after you play.

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
