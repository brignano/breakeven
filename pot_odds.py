#!/usr/bin/env python3
"""Poker Helper: pot odds. A small desktop calculator for Texas Hold'em.

Standard library only (Tkinter). Run with:  python3 pot_odds.py

Three answers, each from what you type in:
  1. Pot odds   — the share of the final pot you are paying, i.e. the equity
                  you need for a call to break even.
  2. Outs       — your chance of hitting, from a count of outs (exact, not
                  the rule of 2 and 4).
  3. Equity     — your chance of winning the hand, simulated against N
                  opponents holding random cards, from your hole cards and
                  the board.
Then it compares the equity you have against the equity you need.
"""

import random
from collections import Counter
from itertools import combinations

RANKS = "23456789TJQKA"
SUITS = "cdhs"
SUIT_SYMBOLS = {"♣": "c", "♦": "d", "♥": "h", "♠": "s"}


# --------------------------------------------------------------------------
# Pure maths: no GUI, so it can be tested on its own.
# --------------------------------------------------------------------------

def pot_odds(pot, call):
    """Equity needed to break even on a call.

    `pot` is everything in the middle *including* the bet you face.
    """
    if call <= 0:
        return 0.0
    return call / (pot + call)


def call_ev(pot, call, equity):
    """Expected value of calling, ignoring future betting."""
    return equity * (pot + call) - call


def outs_probability(outs, board_cards):
    """Exact chance of hitting one of `outs` by the river.

    Returns (next_card, by_river). by_river is None on the turn's next card
    being the river; both are None before the flop or after the river.
    """
    if board_cards not in (3, 4) or outs <= 0:
        return None, None
    unseen = 52 - 2 - board_cards
    outs = min(outs, unseen)
    next_card = outs / unseen
    if board_cards == 4:
        return next_card, None
    miss_both = (unseen - outs) / unseen * (unseen - 1 - outs) / (unseen - 1)
    return next_card, 1 - miss_both


def parse_cards(text):
    """'Ah Kd' / 'AhKd' / 'A♥ 10♦' -> [card ints]. Raises ValueError."""
    for sym, letter in SUIT_SYMBOLS.items():
        text = text.replace(sym, letter)
    text = text.replace("10", "T").replace(",", " ").replace(" ", "")
    if len(text) % 2:
        raise ValueError(f"Can't read cards from {text!r} — use e.g. 'Ah Kd'.")
    cards = []
    for i in range(0, len(text), 2):
        r, s = text[i].upper(), text[i + 1].lower()
        if r not in RANKS or s not in SUITS:
            raise ValueError(f"'{text[i:i+2]}' isn't a card — use e.g. Ah, Td, 7c.")
        cards.append(RANKS.index(r) * 4 + SUITS.index(s))
    if len(set(cards)) != len(cards):
        raise ValueError("The same card appears twice.")
    return cards


def _straight_high(rank_mask):
    """Highest straight in a 13-bit rank mask, or -1. Handles A-2-3-4-5."""
    # Bit r+1 = rank r; bit 0 = the ace again, playing low.
    mask = (rank_mask << 1) | ((rank_mask >> 12) & 1)
    for high in range(13, 3, -1):
        if (mask >> (high - 4)) & 0b11111 == 0b11111:
            return high - 1
    return -1


def hand_rank(cards):
    """Rank of the best 5-card hand in 5–7 cards. Higher tuple wins."""
    ranks = [c // 4 for c in cards]
    suits = [c % 4 for c in cards]

    suit_count = Counter(suits)
    flush_suit = next((s for s, n in suit_count.items() if n >= 5), None)
    if flush_suit is not None:
        fr = sorted((r for r, s in zip(ranks, suits) if s == flush_suit), reverse=True)
        sf = _straight_high(sum(1 << r for r in fr))
        if sf >= 0:
            return (8, sf)

    count = Counter(ranks)
    # Sort ranks by (how many, rank), best first.
    groups = sorted(count.items(), key=lambda kv: (kv[1], kv[0]), reverse=True)
    by_count = [r for r, _ in groups]
    shape = [n for _, n in groups]

    if shape[0] == 4:
        kicker = max(r for r in ranks if r != by_count[0])
        return (7, by_count[0], kicker)
    if shape[0] == 3 and len(shape) > 1 and shape[1] >= 2:
        return (6, by_count[0], by_count[1])
    if flush_suit is not None:
        return (5, *fr[:5])
    st = _straight_high(sum(1 << r for r in count))
    if st >= 0:
        return (4, st)
    if shape[0] == 3:
        return (3, by_count[0], *sorted(by_count[1:], reverse=True)[:2])
    if shape[0] == 2 and shape[1] == 2:
        pairs = sorted((r for r, n in count.items() if n == 2), reverse=True)[:2]
        kicker = max(r for r in ranks if r not in pairs)
        return (2, *pairs, kicker)
    if shape[0] == 2:
        return (1, by_count[0], *sorted(by_count[1:], reverse=True)[:3])
    return (0, *sorted(ranks, reverse=True)[:5])


def simulate_equity(hole, board, opponents, iterations=5000, rng=random):
    """Monte Carlo equity vs `opponents` random hands. Ties split the pot."""
    if len(hole) != 2:
        raise ValueError("Enter exactly two hole cards.")
    if len(board) not in (0, 3, 4, 5):
        raise ValueError("The board has 0, 3, 4 or 5 cards.")
    if set(hole) & set(board):
        raise ValueError("A hole card is also on the board.")
    if not 1 <= opponents <= 9:
        raise ValueError("Opponents must be between 1 and 9.")

    deck = [c for c in range(52) if c not in hole and c not in board]
    need = 5 - len(board)
    share = 0.0
    for _ in range(iterations):
        drawn = rng.sample(deck, need + 2 * opponents)
        full_board = board + drawn[:need]
        mine = hand_rank(hole + full_board)
        best_other = max(
            hand_rank(drawn[need + 2 * i: need + 2 * i + 2] + full_board)
            for i in range(opponents)
        )
        if mine > best_other:
            share += 1
        elif mine == best_other:
            tied = 1 + sum(
                hand_rank(drawn[need + 2 * i: need + 2 * i + 2] + full_board) == mine
                for i in range(opponents)
            )
            share += 1 / tied
    return share / iterations


# --------------------------------------------------------------------------
# GUI
# --------------------------------------------------------------------------

def run_gui():
    import threading
    import tkinter as tk
    from tkinter import ttk

    root = tk.Tk()
    root.title("Poker Helper — Pot Odds")
    root.resizable(False, False)
    frm = ttk.Frame(root, padding=16)
    frm.grid()

    fields = {}

    def row(r, label, key, default="", hint=""):
        ttk.Label(frm, text=label).grid(row=r, column=0, sticky="w", pady=3)
        var = tk.StringVar(value=default)
        ttk.Entry(frm, textvariable=var, width=18).grid(row=r, column=1, sticky="w")
        ttk.Label(frm, text=hint, foreground="gray").grid(row=r, column=2, sticky="w", padx=8)
        fields[key] = var

    ttk.Label(frm, text="The bet", font=("", 11, "bold")).grid(row=0, column=0, sticky="w")
    row(1, "Pot (incl. their bet)", "pot", "100", "everything in the middle now")
    row(2, "To call", "call", "50", "what you'd put in")

    ttk.Label(frm, text="Your hand (optional)", font=("", 11, "bold")).grid(
        row=3, column=0, sticky="w", pady=(12, 0))
    row(4, "Hole cards", "hole", "", "e.g. Ah Kh")
    row(5, "Board", "board", "", "e.g. Qh Jh 2c")
    row(6, "Opponents", "opps", "1", "players still in")
    row(7, "Outs", "outs", "", "optional, e.g. 9 for a flush draw")

    out = tk.Text(frm, width=60, height=12, wrap="word", relief="flat",
                  background=root.cget("background"))
    out.grid(row=9, column=0, columnspan=3, pady=(12, 0))

    def show(text):
        out.configure(state="normal")
        out.delete("1.0", "end")
        out.insert("1.0", text)
        out.configure(state="disabled")

    def num(key, kind=float, required=True):
        raw = fields[key].get().strip().replace("$", "").replace(",", "")
        if not raw:
            if required:
                raise ValueError(f"Fill in '{key}'.")
            return None
        return kind(raw)

    def calculate():
        try:
            pot, call = num("pot"), num("call")
            if pot < 0 or call < 0:
                raise ValueError("Amounts can't be negative.")
            needed = pot_odds(pot, call)
            lines = [
                f"Pot odds: {pot:g} to {call:g}  ({pot / call:.2f} : 1)" if call else "Nothing to call.",
                f"You need {needed:.1%} equity to break even.",
            ]

            hole_txt, board_txt = fields["hole"].get().strip(), fields["board"].get().strip()
            hole = parse_cards(hole_txt) if hole_txt else []
            board = parse_cards(board_txt) if board_txt else []

            outs = num("outs", int, required=False)
            if outs is not None:
                nxt, river = outs_probability(outs, len(board))
                if nxt is None:
                    lines.append("\nOuts: enter a 3- or 4-card board to use outs.")
                else:
                    lines.append(f"\nOuts ({outs}): {nxt:.1%} on the next card"
                                 + (f", {river:.1%} by the river" if river is not None else ""))
                    lines.append(_verdict(nxt, needed, pot, call, "next card"))

            if not hole:
                show("\n".join(lines))
                return

            opps = num("opps", int)
            show("\n".join(lines) + "\n\nSimulating…")
            btn.state(["disabled"])

            def work():
                try:
                    eq = simulate_equity(hole, board, opps)
                    extra = (f"\n\nEquity vs {opps} random hand{'s' * (opps > 1)}: {eq:.1%}"
                             f"\n{_verdict(eq, needed, pot, call, 'showdown')}")
                    root.after(0, show, "\n".join(lines) + extra)
                except ValueError as e:
                    root.after(0, show, f"⚠ {e}")
                finally:
                    root.after(0, btn.state, ["!disabled"])

            threading.Thread(target=work, daemon=True).start()
        except ValueError as e:
            show(f"⚠ {e}")

    btn = ttk.Button(frm, text="Calculate", command=calculate)
    btn.grid(row=8, column=0, columnspan=3, pady=(12, 0), sticky="ew")
    root.bind("<Return>", lambda _e: calculate())
    calculate()
    root.mainloop()


def _verdict(equity, needed, pot, call, basis):
    ev = call_ev(pot, call, equity)
    word = "CALL" if equity >= needed else "FOLD (on pot odds alone)"
    return f"→ {word}: {equity:.1%} vs {needed:.1%} needed, EV {ev:+.2f} ({basis})"


if __name__ == "__main__":
    run_gui()
