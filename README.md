# Poker Helper

A desktop helper for Texas Hold'em. It starts with a pot odds calculator: enter the pot and the bet, plus your cards if you like, and it tells you whether calling pays.

## Download

Go to **Releases** on the right side of this page and download the latest version:

- **Windows:** `PokerHelper-windows.zip`. Unzip it and double-click `Poker Helper.exe`.
- **Mac:** `PokerHelper-mac.zip`. Unzip it and drag `Poker Helper` into Applications.

You don't need to install Python or anything else.

**First launch:** the app isn't signed (signing costs money every year), so your computer will warn you the first time you open it.

- **Windows** shows "Windows protected your PC". Click **More info**, then **Run anyway**.
- **Mac** says the app "can't be opened". Open **System Settings → Privacy & Security**, scroll down, and click **Open Anyway**. On older macOS versions, right-click the app and choose **Open** instead.

You only have to do this once. The Mac build runs on Apple Silicon Macs (M1 and later).

## What you type in

| Field | Meaning |
|---|---|
| Pot | Everything in the middle, **including the bet you're facing** |
| To call | What you would put in |
| Hole cards | Optional. Use `Ah Kh` or `A♥ K♥`. `10` and `T` both mean ten |
| Board | Optional. Enter 0, 3, 4 or 5 cards |
| Opponents | The number of players still in the hand |
| Outs | Optional. For example, 9 for a flush draw or 8 for an open-ended straight draw |

## What you get back

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

**Releasing:** push a tag such as `v1.0.0`. GitHub Actions runs the tests, builds the Windows and Mac apps with PyInstaller, and attaches both zips to a release for that tag. Every push to `main` also builds them, and you can download those builds from the Actions run.
