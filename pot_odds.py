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


def next_card_equities(hole, board, opponents, iterations=300, rng=random,
                       stop=lambda: False):
    """Equity with each possible next card dealt: {card: equity}.

    Only on the flop or turn; empty otherwise, or if `stop()` turns true.
    """
    if len(board) not in (3, 4):
        return {}
    result = {}
    for card in range(52):
        if card in hole or card in board:
            continue
        if stop():
            return {}
        result[card] = simulate_equity(hole, board + [card], opponents, iterations, rng)
    return result


# How far one card has to lift your equity to count as an out, or as a help,
# and how far it has to drop it to count as a danger card.
OUT_JUMP, HELP_JUMP, DANGER_DROP = 0.15, 0.05, 0.10


def classify_next_cards(equities, current, needed):
    """Split next cards into outs, helpers and danger cards.

    An out lifts your equity by OUT_JUMP and leaves you with at least the
    equity a call needs. A helper lifts it by HELP_JUMP but isn't an out.
    A danger card helps the other players: it drops your equity by
    DANGER_DROP, or by HELP_JUMP when that takes a call from paying to not.
    """
    outs = {c for c, e in equities.items() if e >= needed and e >= current + OUT_JUMP}
    helps = {c for c, e in equities.items() if c not in outs and e >= current + HELP_JUMP}
    dangers = {c for c, e in equities.items()
               if e <= current - DANGER_DROP
               or (e <= current - HELP_JUMP and e < needed <= current)}
    return outs, helps, dangers


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
# GUI: plain Tk widgets with our own colours and canvas-drawn cards, so it
# looks the same on Windows and Mac instead of like a system dialog.
# --------------------------------------------------------------------------

# Seven card slots: two hole cards, then the board in dealing order.
SLOT_GROUPS = [("YOUR HAND", 0, 2), ("FLOP", 2, 5), ("TURN", 5, 6), ("RIVER", 6, 7)]
COMMON_OUTS = [("Flush draw", 9), ("Open-ended", 8), ("Gutshot", 4)]

THEME = {
    "bg": "#0d1410", "felt": "#17573a", "felt_dark": "#11432c", "felt_line": "#2c7a52",
    "text": "#f3f6f4", "muted": "#a6c8b3", "gold": "#f2c14e",
    "card": "#fbfaf6", "red": "#d32f2f", "black": "#1d1d1f",
    "used": "#1e4a33", "used_text": "#3f7a5a",
    "out": "#fff1bf", "help": "#e3f4e8", "help_line": "#23a55a", "hover": "#2b6cb0",
    "danger": "#f9d3cd", "danger_line": "#c94235",
    "call": "#23a55a", "fold": "#c94235", "neutral": "#255c40", "warn": "#b07a12",
}


def _rounded_rect(cv, x1, y1, x2, y2, r, **kw):
    pts = [x1 + r, y1, x1 + r, y1, x2 - r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
           x2, y1 + r, x2, y2 - r, x2, y2 - r, x2, y2, x2 - r, y2, x2 - r, y2,
           x1 + r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y2 - r, x1, y1 + r,
           x1, y1 + r, x1, y1]
    return cv.create_polygon(pts, smooth=True, **kw)


def run_gui():
    import threading
    import tkinter as tk
    import tkinter.font as tkfont

    T = THEME
    root = tk.Tk()
    root.title("Poker Helper")
    root.configure(bg=T["bg"])
    root.minsize(1, 1)

    families = set(tkfont.families())
    family = next((f for f in ("Segoe UI", "SF Pro Text", "Helvetica Neue", "Inter",
                               "DejaVu Sans") if f in families), "Helvetica")

    # Everything is drawn at a base size times `scale`, which follows the
    # window size. Fonts are shared objects, so resizing one updates every
    # widget and canvas text that uses it.
    scale = [1.0]
    fonts = {}

    def font(size, weight="normal"):
        if (size, weight) not in fonts:
            fonts[size, weight] = tkfont.Font(family=family, size=size, weight=weight)
        return fonts[size, weight]

    def px(v):
        return v * scale[0]

    def label(parent, text="", size=10, weight="normal", fg=T["muted"], **kw):
        return tk.Label(parent, text=text, font=font(size, weight), fg=fg,
                        bg=parent["bg"], **kw)

    def pill(parent, text, command, size=10):
        """A flat clickable button. Tk buttons ignore colours on macOS; labels don't."""
        w = tk.Label(parent, text=text, font=font(size, "bold"), fg=T["text"],
                     bg=T["felt_dark"], padx=10, pady=4, cursor="hand2")
        w.bind("<Button-1>", lambda _e: command())
        w.bind("<Enter>", lambda _e: w.configure(bg=T["felt_line"]))
        w.bind("<Leave>", lambda _e: w.configure(bg=T["felt_dark"]))
        return w

    outer = tk.Frame(root, bg=T["bg"], padx=18, pady=14)
    outer.pack(expand=True)

    head = tk.Frame(outer, bg=T["bg"])
    head.pack(fill="x", pady=(0, 10))
    label(head, "♠ Poker Helper", 17, "bold", fg=T["text"]).pack(side="left")
    label(head, "pot odds & equity", 10).pack(side="left", padx=10, pady=(6, 0))

    felt = tk.Frame(outer, bg=T["felt"], padx=18, pady=14,
                    highlightthickness=2, highlightbackground=T["felt_line"])
    felt.pack(fill="x")

    # ---- Top row: amounts, opponents, pot odds ---------------------------
    top = tk.Frame(felt, bg=T["felt"])
    top.pack(fill="x")
    fields = {}

    def amount(col, caption, key, default):
        box = tk.Frame(top, bg=T["felt"])
        box.grid(row=0, column=col, sticky="w", padx=(0, 18))
        label(box, caption, 9, "bold").pack(anchor="w")
        var = tk.StringVar(value=default)
        tk.Entry(box, textvariable=var, width=7, font=font(16, "bold"), fg=T["text"],
                 bg=T["felt_dark"], insertbackground=T["text"], relief="flat",
                 highlightthickness=1, highlightbackground=T["felt_line"],
                 highlightcolor=T["gold"]).pack(anchor="w", ipady=3)
        fields[key] = var

    amount(0, "POT (INCL. THEIR BET)", "pot", "100")
    amount(1, "TO CALL", "call", "50")

    def stepper(parent, var, lo, hi):
        box = tk.Frame(parent, bg=T["felt"])
        shown = label(box, str(var.get()), 16, "bold", fg=T["text"], width=2)

        def step(d):
            var.set(min(hi, max(lo, var.get() + d)))
            shown.configure(text=str(var.get()))
            if var is outs:
                outs_manual[0], outs_auto[0] = True, False
            schedule()

        pill(box, "−", lambda: step(-1), 12).pack(side="left")
        shown.pack(side="left", padx=4)
        pill(box, "+", lambda: step(1), 12).pack(side="left")
        var.trace_add("write", lambda *_: shown.configure(text=str(var.get())))
        return box

    opps = tk.IntVar(value=1)
    # On the flop and turn, outs are counted from your cards unless you set
    # them yourself. A new spot (other cards or opponents) counts afresh.
    outs = tk.IntVar(value=0)
    outs_manual = [False]   # the user set the count for this spot
    outs_auto = [False]     # the count on show came from the cards
    spot = [None]
    obox = tk.Frame(top, bg=T["felt"])
    obox.grid(row=0, column=2, sticky="w")
    label(obox, "OPPONENTS", 9, "bold").pack(anchor="w")
    stepper(obox, opps, 1, 9).pack(anchor="w", pady=(2, 0))

    odds_box = tk.Frame(top, bg=T["felt"])
    odds_box.grid(row=0, column=3, sticky="e")
    top.grid_columnconfigure(3, weight=1)
    odds_big = label(odds_box, "", 18, "bold", fg=T["gold"])
    odds_big.pack(anchor="e")
    odds_small = label(odds_box, "", 9)
    odds_small.pack(anchor="e")

    # ---- Card slots -------------------------------------------------------
    slots = [None] * 7
    active = [0]
    SW, SH, GAP, GROUP_GAP, SLOT_TOP = 58, 80, 8, 22, 18   # at scale 1

    def slot_xs():
        xs, x = [], 2
        for _name, start, end in SLOT_GROUPS:
            for _i in range(start, end):
                xs.append(px(x))
                x += SW + GAP
            x += GROUP_GAP - GAP
        return xs, px(x)

    slot_row = tk.Frame(felt, bg=T["felt"])
    slot_row.pack(fill="x", pady=(14, 0))
    slot_cv = tk.Canvas(slot_row, bg=T["felt"], highlightthickness=0)
    slot_cv.pack(side="left")
    pill(slot_row, "Clear", lambda: clear_cards()).pack(side="right", anchor="s", pady=(0, 2))

    def ink(card):
        return T["red"] if card % 4 in (1, 2) else T["black"]

    def draw_slots():
        slot_cv.delete("all")
        xs, _ = slot_xs()
        sw, sh, y0 = px(SW), px(SH), px(SLOT_TOP)
        for name, start, _end in SLOT_GROUPS:
            slot_cv.create_text(xs[start], px(6), text=name, anchor="w",
                                font=font(8, "bold"), fill=T["muted"])
        for i, x0 in enumerate(xs):
            card = slots[i]
            if card is None:
                outline = T["gold"] if i == active[0] else T["felt_line"]
                _rounded_rect(slot_cv, x0, y0, x0 + sw, y0 + sh, px(9), fill=T["felt_dark"],
                              outline=outline, width=2 if i == active[0] else 1,
                              dash=() if i == active[0] else (4, 3))
                if i == active[0]:
                    slot_cv.create_text(x0 + sw / 2, y0 + sh / 2, text="+",
                                        font=font(18), fill=T["gold"])
            else:
                rank, suit = card_label(card)[:-1], card_label(card)[-1]
                _rounded_rect(slot_cv, x0, y0, x0 + sw, y0 + sh, px(9), fill=T["card"],
                              outline=T["gold"] if i == active[0] else "#d9d6cc",
                              width=2 if i == active[0] else 1)
                slot_cv.create_text(x0 + px(8), y0 + px(6), text=rank, anchor="nw",
                                    font=font(13, "bold"), fill=ink(card))
                slot_cv.create_text(x0 + sw / 2, y0 + sh / 2 + px(10), text=suit,
                                    font=font(24), fill=ink(card))
        slot_cv.configure(cursor="hand2")

    # Clicks are matched by position, not bound to canvas items, because every
    # redraw replaces the items and a click on a just-replaced item is lost.
    def slot_at(event):
        for i, x0 in enumerate(slot_xs()[0]):
            if x0 <= event.x <= x0 + px(SW) and px(SLOT_TOP) <= event.y <= px(SLOT_TOP + SH):
                return i
        return None

    slot_cv.bind("<Button-1>", lambda e: slot_at(e) is not None and click_slot(slot_at(e)))

    # ---- Verdict banner ---------------------------------------------------
    DW, DH, DG = 42, 50, 5                      # deck card size and gap, at scale 1
    BW, BH = 13 * (DW + DG) - DG + 2, 92
    banner = tk.Canvas(felt, bg=T["felt"], highlightthickness=0)
    banner.pack(pady=(12, 0), anchor="w")
    detail = label(felt, "", 10, justify="left", anchor="w")
    detail.pack(fill="x", pady=(6, 0))

    shown_banner = [None]

    def draw_banner(*args):
        shown_banner[0] = args
        paint_banner(*args)

    def paint_banner(word, colour, headline, sub="", equity=None, needed=None):
        banner.delete("all")
        bw, bh = px(BW), px(BH)
        _rounded_rect(banner, 1, 1, bw - 1, bh - 1, px(14), fill=colour, outline="")
        banner.create_text(px(22), px(34), text=word, anchor="w", font=font(26, "bold"),
                           fill="white")
        banner.create_text(px(170), px(26), text=headline, anchor="w",
                           font=font(13, "bold"), fill="white")
        banner.create_text(px(170), px(48), text=sub, anchor="w", font=font(10),
                           fill="#e9f3ec")
        if equity is not None:
            # Equity bar, with a tick where the call breaks even.
            bx1, bx2, by, bt = px(22), bw - px(22), px(72), px(8)
            banner.create_rectangle(bx1, by, bx2, by + bt, fill="#0b2a1b", outline="")
            banner.create_rectangle(bx1, by, bx1 + (bx2 - bx1) * equity, by + bt,
                                    fill="white", outline="")
            nx = bx1 + (bx2 - bx1) * needed
            banner.create_line(nx, by - px(4), nx, by + bt + px(4), fill=T["gold"],
                               width=px(3))

    def verdict(equity, needed, pot, call, basis):
        ev = call_ev(pot, call, equity)
        good = equity >= needed
        draw_banner("CALL" if good else "FOLD", T["call"] if good else T["fold"],
                    f"{equity:.1%} {basis}  ·  need {needed:.1%}",
                    f"EV of calling {ev:+.2f}" + ("" if good else "  ·  on pot odds alone"),
                    equity, needed)

    # ---- The deck ---------------------------------------------------------
    deck_head = tk.Frame(felt, bg=T["felt"])
    deck_head.pack(fill="x", pady=(14, 4))
    deck_title = label(deck_head, "", 9, "bold")
    deck_title.pack(side="left")
    deck_info = label(deck_head, "", 9, "bold", fg=T["gold"])
    deck_info.pack(side="right")
    deck_cv = tk.Canvas(felt, bg=T["felt"], highlightthickness=0, cursor="hand2")
    deck_cv.pack(anchor="w")
    hover = [None]
    # Next-card highlights: {"eq": {card: equity}, "now": equity before it,
    # "outs": set, "helps": set, "dangers": set}.
    marks = {"eq": {}, "now": None, "outs": set(), "helps": set(), "dangers": set()}

    def set_marks(eq=None, now=None, outs_=(), helps=(), dangers=()):
        marks.update(eq=eq or {}, now=now, outs=set(outs_), helps=set(helps),
                     dangers=set(dangers))
        if marks["eq"]:
            deck_title.configure(text=f"DECK — {len(marks['outs'])} outs in gold, "
                                      f"{len(marks['helps'])} helpers in green, "
                                      f"{len(marks['dangers'])} danger cards in red")
        else:
            deck_title.configure(text="DECK — click a card to put it in the gold slot")
        draw_deck()
        show_hover_info()

    def show_hover_info():
        c = hover[0]
        if c is not None and c in marks["eq"]:
            e = marks["eq"][c]
            deck_info.configure(text=f"{card_label(c)} next: {e:.0%} to win "
                                     f"({(e - marks['now']) * 100:+.0f} pts)")
        else:
            deck_info.configure(text="point at a card" if marks["eq"] else "")

    def draw_deck():
        deck_cv.delete("all")
        used = set(slots)
        dw, dh, step_ = px(DW), px(DH), px(DW + DG)
        for row_i, suit in enumerate("shdc"):               # spades, hearts, diamonds, clubs
            for col_i, rank in enumerate(reversed(RANKS)):  # A down to 2
                card = RANKS.index(rank) * 4 + SUITS.index(suit)
                x0, y0 = col_i * step_ + 1, row_i * px(DH + DG) + 1
                if card in used:
                    fill, fg, outline = T["used"], T["used_text"], T["used"]
                elif card in marks["outs"]:
                    fill, fg, outline = T["out"], ink(card), T["gold"]
                elif card in marks["helps"]:
                    fill, fg, outline = T["help"], ink(card), T["help_line"]
                elif card in marks["dangers"]:
                    fill, fg, outline = T["danger"], ink(card), T["danger_line"]
                else:
                    fill, fg, outline = T["card"], ink(card), "#d9d6cc"
                if hover[0] == card and card not in used:
                    outline = T["hover"]
                strong = card in marks["outs"] or card in marks["dangers"]
                lit = strong or card in marks["helps"] or hover[0] == card
                _rounded_rect(deck_cv, x0, y0, x0 + dw, y0 + dh, px(7), fill=fill,
                              outline=outline, width=3 if strong else 2 if lit else 1)
                deck_cv.create_text(x0 + dw / 2, y0 + px(16), text=card_label(card)[:-1],
                                    font=font(12, "bold"), fill=fg)
                deck_cv.create_text(x0 + dw / 2, y0 + px(35), text=card_label(card)[-1],
                                    font=font(14), fill=fg)

    def card_at(event):
        col, row = int(event.x // px(DW + DG)), int(event.y // px(DH + DG))
        if not (0 <= col < 13 and 0 <= row < 4) or event.x % px(DW + DG) > px(DW):
            return None
        return (12 - col) * 4 + SUITS.index("shdc"[row])

    def set_hover(card):
        if hover[0] != card:
            hover[0] = card
            draw_deck()
            show_hover_info()

    deck_cv.bind("<Button-1>", lambda e: card_at(e) is not None and pick(card_at(e)))
    deck_cv.bind("<Motion>", lambda e: set_hover(card_at(e)))
    deck_cv.bind("<Leave>", lambda _e: set_hover(None))

    # ---- Outs -------------------------------------------------------------
    outs_row = tk.Frame(felt, bg=T["felt"])
    outs_row.pack(fill="x", pady=(12, 0))
    label(outs_row, "OUTS", 9, "bold").pack(side="left", padx=(0, 8))
    stepper(outs_row, outs, 0, 20).pack(side="left")

    def preset(n):
        outs.set(n)
        outs_manual[0], outs_auto[0] = True, False
        schedule()

    for name, n in COMMON_OUTS:
        pill(outs_row, f"{name} · {n}", lambda n=n: preset(n)).pack(side="left", padx=(8, 0))
    outs_hint = label(outs_row, "optional", 9)
    outs_hint.pack(side="right")

    # ---- Interaction ------------------------------------------------------
    def redraw_cards():
        draw_slots()
        draw_deck()
        schedule()

    def pick(card):
        if card in slots:                # clicking a used card takes it back
            i = slots.index(card)
            slots[i] = None
            active[0] = i
        else:
            slots[active[0]] = card
            active[0] = next_empty_slot(slots, active[0])
        redraw_cards()

    def click_slot(i):
        slots[i] = None
        active[0] = i
        redraw_cards()

    def clear_cards():
        slots[:] = [None] * 7
        active[0] = 0
        redraw_cards()

    def num(key, name):
        raw = fields[key].get().strip().replace("$", "").replace(",", "")
        if not raw:
            raise ValueError(f"Fill in the {name}.")
        try:
            return float(raw)
        except ValueError:
            raise ValueError(f"The {name} should be a number.") from None

    # Results update as you go. Each run gets a number, so a slow simulation
    # that finishes after a newer one started is thrown away.
    run_id = [0]
    pending = [None]

    def schedule():
        if pending[0] is not None:
            root.after_cancel(pending[0])
        pending[0] = root.after(150, calculate)

    def calculate():
        pending[0] = None
        run_id[0] += 1
        me = run_id[0]
        try:
            pot, call = num("pot", "pot"), num("call", "amount to call")
            if pot < 0 or call < 0:
                raise ValueError("Amounts can't be negative.")
        except ValueError as e:
            odds_big.configure(text="—")
            odds_small.configure(text="")
            detail.configure(text="")
            draw_banner("?", T["warn"], str(e), "Type the pot and the bet you face.")
            return

        needed = pot_odds(pot, call)
        odds_big.configure(text=f"{pot / call:.2f} : 1" if call else "free")
        odds_small.configure(text=f"need {needed:.1%} equity")

        hole = [c for c in slots[:2] if c is not None]
        board = [c for c in slots[2:] if c is not None]
        can_sim = len(hole) == 2 and len(board) in (0, 3, 4, 5)
        auto = can_sim and len(board) in (3, 4)
        if auto:
            key = (tuple(hole), tuple(board), opps.get())
            if key != spot[0]:
                spot[0], outs_manual[0] = key, False
        else:
            spot[0] = None
            if outs_auto[0]:        # a count from cards no longer on the table
                outs.set(0)
                outs_auto[0] = False
        set_marks()

        def outs_note(n):
            nxt, river = outs_probability(n, len(board))
            if not n:
                return None, None
            if nxt is None:
                return "Outs need the flop (or flop and turn) on the board.", None
            return (f"{n} outs: {nxt:.1%} on the next card"
                    + (f", {river:.1%} by the river" if river is not None else "")), nxt

        notes = []
        if (hole or board) and not can_sim:
            notes.append("Pick both hole cards, and 0, 3, 4 or 5 board cards, to see your equity.")

        def show_notes(n):
            text, hit = outs_note(n)
            detail.configure(text="   ·   ".join(([text] if text else []) + notes))
            return hit

        # A count from the cards waits until the new one is ready.
        outs_hit = show_notes(0 if auto and not outs_manual[0] else outs.get())
        outs_hint.configure(text="set by hand" if outs_manual[0] else
                            "counting…" if auto else "optional")

        def fallback():
            if not call:
                draw_banner("CHECK", T["call"], "Nothing to call", "It costs nothing to see more cards.")
            elif outs_hit is not None:
                verdict(outs_hit, needed, pot, call, "to hit next card")
            else:
                draw_banner("NEED", T["neutral"], f"{needed:.1%} equity to call",
                            "Pick your cards or set your outs to get a verdict.",
                            0.0, needed)

        if not can_sim:
            fallback()
            return

        n_opps = opps.get()
        draw_banner("…", T["neutral"], "Simulating",
                    f"5,000 hands against {n_opps} random hand{'s' * (n_opps > 1)}")

        def work():
            try:
                eq = simulate_equity(hole, board, n_opps)
            except ValueError as e:
                root.after(0, lambda: run_id[0] == me and draw_banner("?", T["warn"], str(e)))
                return

            def done():
                if run_id[0] != me:
                    return
                if call:
                    verdict(eq, needed, pot, call,
                            f"to win vs {n_opps} hand{'s' * (n_opps > 1)}")
                else:
                    draw_banner("CHECK", T["call"], f"{eq:.1%} to win",
                                "Nothing to call.", eq, 0.0)
            root.after(0, done)
            if not auto:
                return

            # Then try every possible next card, to light up the outs.
            per_card = next_card_equities(hole, board, n_opps, stop=lambda: run_id[0] != me)

            def marked():
                if run_id[0] != me or not per_card:
                    return
                outs_, helps, dangers = classify_next_cards(per_card, eq, needed)
                set_marks(per_card, eq, outs_, helps, dangers)
                if not outs_manual[0]:
                    outs.set(len(outs_))
                    outs_auto[0] = True
                    show_notes(len(outs_))
                    outs_hint.configure(text="from your cards")
            root.after(0, marked)

        threading.Thread(target=work, daemon=True).start()

    for var in fields.values():
        var.trace_add("write", lambda *_: schedule())
    def apply_scale():
        for (size, _weight), f in fonts.items():
            f.configure(size=max(1, round(size * scale[0])))
        slot_cv.configure(width=slot_xs()[1], height=px(SLOT_TOP + SH + 4))
        banner.configure(width=px(BW), height=px(BH))
        detail.configure(wraplength=px(BW))
        deck_cv.configure(width=px(13 * (DW + DG)), height=px(4 * (DH + DG)))
        draw_slots()
        draw_deck()
        if shown_banner[0]:
            paint_banner(*shown_banner[0])

    # Grow everything with the window, never below the size it opens at.
    # Padding doesn't scale, so the scaled content always fits.
    base = [None]
    resize_pending = [None]

    def on_resize(event):
        if event.widget is not root or base[0] is None:
            return
        if resize_pending[0] is not None:
            root.after_cancel(resize_pending[0])
        resize_pending[0] = root.after(40, rescale)

    def rescale():
        resize_pending[0] = None
        bw, bh = base[0]
        new = max(1.0, min(root.winfo_width() / bw, root.winfo_height() / bh))
        if abs(new - scale[0]) > 0.02:
            scale[0] = new
            apply_scale()

    apply_scale()
    calculate()
    root.update_idletasks()
    base[0] = (root.winfo_reqwidth(), root.winfo_reqheight())
    root.minsize(*base[0])
    root.bind("<Configure>", on_resize)
    root.mainloop()


if __name__ == "__main__":
    run_gui()
