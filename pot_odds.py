#!/usr/bin/env python3
"""Poker Helper: pot odds. A small desktop calculator for Texas Hold'em.

Standard library only (Tkinter). Run with:  python3 pot_odds.py

Three answers, from the amounts you type and the cards you click:
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


def card_label(card):
    """Card int -> 'A♠' / '10♥', for display."""
    return RANKS[card // 4].replace("T", "10") + "♣♦♥♠"[card % 4]


def next_empty_slot(slots, after):
    """Index of the first empty slot after `after` (wrapping), or `after`."""
    n = len(slots)
    for step in range(1, n + 1):
        i = (after + step) % n
        if slots[i] is None:
            return i
    return after


# --------------------------------------------------------------------------
# GUI
# --------------------------------------------------------------------------

# Seven card slots: two hole cards, then the board in dealing order.
SLOT_GROUPS = [("Your hand", 0, 2), ("Flop", 2, 5), ("Turn", 5, 6), ("River", 6, 7)]
COMMON_OUTS = [("Flush draw", 9), ("Open-ended", 8), ("Gutshot", 4), ("None", 0)]


def run_gui():
    import threading
    import tkinter as tk
    from tkinter import ttk

    root = tk.Tk()
    root.title("Poker Helper — Pot Odds")
    root.resizable(False, False)
    frm = ttk.Frame(root, padding=16)
    frm.grid()

    def heading(r, text):
        ttk.Label(frm, text=text, font=("", 11, "bold")).grid(
            row=r, column=0, columnspan=3, sticky="w", pady=(12 if r else 0, 2))

    # ---- The bet: amounts are still typed, they're just numbers ----------
    heading(0, "The bet")
    fields = {}
    for r, (label, key, default, hint) in enumerate([
        ("Pot (incl. their bet)", "pot", "100", "everything in the middle now"),
        ("To call", "call", "50", "what you'd put in"),
    ], start=1):
        ttk.Label(frm, text=label).grid(row=r, column=0, sticky="w", pady=3)
        var = tk.StringVar(value=default)
        ttk.Entry(frm, textvariable=var, width=12).grid(row=r, column=1, sticky="w")
        ttk.Label(frm, text=hint, foreground="gray").grid(row=r, column=2, sticky="w", padx=8)
        fields[key] = var

    # ---- Cards: click a slot, then click a card in the deck ---------------
    heading(3, "Your cards (optional) — click a card to place it")
    slots = [None] * 7
    active = [0]

    slot_box = ttk.Frame(frm)
    slot_box.grid(row=4, column=0, columnspan=3, sticky="w")
    slot_widgets = []
    col = 0
    for name, start, end in SLOT_GROUPS:
        ttk.Label(slot_box, text=name, foreground="gray").grid(
            row=0, column=col, columnspan=end - start, sticky="w", padx=(0 if col == 0 else 14, 0))
        for i in range(start, end):
            w = tk.Label(slot_box, width=4, height=2, font=("", 15, "bold"),
                         relief="solid", bd=1, cursor="hand2")
            w.grid(row=1, column=col, padx=(14 if i == start and col else 2, 2), pady=2)
            w.bind("<Button-1>", lambda _e, i=i: click_slot(i))
            slot_widgets.append(w)
            col += 1
    ttk.Button(slot_box, text="Clear cards", command=lambda: clear_cards()).grid(
        row=1, column=col, padx=(18, 0))

    deck = ttk.Frame(frm)
    deck.grid(row=5, column=0, columnspan=3, sticky="w", pady=(8, 0))
    deck_widgets = {}
    for row_i, suit in enumerate("shdc"):             # spades, hearts, diamonds, clubs
        for col_i, rank in enumerate(reversed(RANKS)):  # A down to 2
            card = RANKS.index(rank) * 4 + SUITS.index(suit)
            w = tk.Label(deck, text=card_label(card), width=3, font=("", 12, "bold"),
                         relief="raised", bd=1, cursor="hand2")
            w.grid(row=row_i, column=col_i, padx=1, pady=1, ipady=3)
            w.bind("<Button-1>", lambda _e, c=card: pick(c))
            deck_widgets[card] = w

    def ink(card):
        return "#c62828" if card % 4 in (1, 2) else "#111111"

    def refresh_cards():
        for i, w in enumerate(slot_widgets):
            card = slots[i]
            bg = "#fff4c2" if i == active[0] else "white"
            if card is None:
                w.configure(text="", bg=bg)
            else:
                w.configure(text=card_label(card), fg=ink(card), bg=bg)
        used = set(slots)
        for card, w in deck_widgets.items():
            if card in used:
                w.configure(fg="#bbbbbb", bg="#e8e8e8", relief="flat")
            else:
                w.configure(fg=ink(card), bg="white", relief="raised")

    def pick(card):
        if card in slots:                # clicking a used card takes it back
            i = slots.index(card)
            slots[i] = None
            active[0] = i
        else:
            slots[active[0]] = card
            active[0] = next_empty_slot(slots, active[0])
        refresh_cards()
        schedule()

    def click_slot(i):
        slots[i] = None
        active[0] = i
        refresh_cards()
        schedule()

    def clear_cards():
        slots[:] = [None] * 7
        active[0] = 0
        refresh_cards()
        schedule()

    # ---- Opponents and outs: spinners and presets, no typing needed ------
    heading(6, "The table")
    opps = tk.IntVar(value=1)
    ttk.Label(frm, text="Opponents").grid(row=7, column=0, sticky="w", pady=3)
    ttk.Spinbox(frm, from_=1, to=9, textvariable=opps, width=4, state="readonly",
                command=lambda: schedule()).grid(row=7, column=1, sticky="w")
    ttk.Label(frm, text="players still in", foreground="gray").grid(
        row=7, column=2, sticky="w", padx=8)

    outs = tk.IntVar(value=0)
    ttk.Label(frm, text="Outs").grid(row=8, column=0, sticky="w", pady=3)
    ttk.Spinbox(frm, from_=0, to=20, textvariable=outs, width=4, state="readonly",
                command=lambda: schedule()).grid(row=8, column=1, sticky="w")
    presets = ttk.Frame(frm)
    presets.grid(row=8, column=2, sticky="w", padx=8)
    for i, (name, n) in enumerate(COMMON_OUTS):
        label = f"{name} ({n})" if n else name
        ttk.Button(presets, text=label, width=len(label) + 1,
                   command=lambda n=n: (outs.set(n), schedule())).grid(row=0, column=i, padx=1)

    out = tk.Text(frm, width=72, height=9, wrap="word", relief="flat",
                  background=root.cget("background"))
    out.grid(row=9, column=0, columnspan=3, pady=(12, 0), sticky="w")

    def show(text):
        out.configure(state="normal")
        out.delete("1.0", "end")
        out.insert("1.0", text)
        out.configure(state="disabled")

    def num(key):
        raw = fields[key].get().strip().replace("$", "").replace(",", "")
        if not raw:
            raise ValueError(f"Fill in '{key}'.")
        return float(raw)

    # Results update as you go. Each run gets a number, so a slow simulation
    # that finishes after a newer one started is thrown away.
    run_id = [0]
    pending = [None]

    def schedule():
        if pending[0] is not None:
            root.after_cancel(pending[0])
        pending[0] = root.after(200, calculate)

    def calculate():
        pending[0] = None
        run_id[0] += 1
        me = run_id[0]
        try:
            pot, call = num("pot"), num("call")
            if pot < 0 or call < 0:
                raise ValueError("Amounts can't be negative.")
            needed = pot_odds(pot, call)
            lines = [
                f"Pot odds: {pot:g} to {call:g}  ({pot / call:.2f} : 1)" if call else "Nothing to call.",
                f"You need {needed:.1%} equity to break even.",
            ]

            hole = [c for c in slots[:2] if c is not None]
            board = [c for c in slots[2:] if c is not None]

            n_outs = outs.get()
            if n_outs:
                nxt, river = outs_probability(n_outs, len(board))
                if nxt is None:
                    lines.append("\nOuts: pick the flop (and turn) to use outs.")
                else:
                    lines.append(f"\nOuts ({n_outs}): {nxt:.1%} on the next card"
                                 + (f", {river:.1%} by the river" if river is not None else ""))
                    lines.append(_verdict(nxt, needed, pot, call, "next card"))

            if len(hole) < 2 or len(board) in (1, 2):
                if hole or board:
                    lines.append("\nPick both hole cards and 0, 3, 4 or 5 board cards for equity.")
                show("\n".join(lines))
                return

            n_opps = opps.get()
            show("\n".join(lines) + "\n\nSimulating…")

            def work():
                try:
                    eq = simulate_equity(hole, board, n_opps)
                    text = ("\n".join(lines)
                            + f"\n\nEquity vs {n_opps} random hand{'s' * (n_opps > 1)}: {eq:.1%}"
                            + f"\n{_verdict(eq, needed, pot, call, 'showdown')}")
                except ValueError as e:
                    text = f"⚠ {e}"
                root.after(0, lambda: run_id[0] == me and show(text))

            threading.Thread(target=work, daemon=True).start()
        except ValueError as e:
            show(f"⚠ {e}")

    for var in fields.values():
        var.trace_add("write", lambda *_: schedule())
    refresh_cards()
    calculate()
    root.mainloop()


def _verdict(equity, needed, pot, call, basis):
    ev = call_ev(pot, call, equity)
    word = "CALL" if equity >= needed else "FOLD (on pot odds alone)"
    return f"→ {word}: {equity:.1%} vs {needed:.1%} needed, EV {ev:+.2f} ({basis})"


if __name__ == "__main__":
    run_gui()
