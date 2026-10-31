#!/usr/bin/env python3
"""Breakeven: pot odds and equity for Texas Hold'em, on your desktop.

Standard library only (Tkinter). Run with:  python3 breakeven.py

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

import os
import random
import re
import statistics
import subprocess
import sys
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


def step_amount(amount, blind, times):
    """`amount` moved by `times` blinds, never below zero."""
    return max(0.0, amount + times * blind)


def format_amount(value):
    """An amount as you'd type it: 12 rather than 12.0, at most two decimals."""
    return f"{value:.2f}".rstrip("0").rstrip(".")


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


def next_card_equities(hole, board, opponents, iterations=600, rng=random,
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


def next_card_baseline(equities):
    """Your equity after a typical next card: the median over all of them.

    Cards are judged against this, not against your equity now. With two
    cards to come, a blank costs a drawing hand one of its two chances, so
    every blank would look like a danger card (and help a made hand).
    """
    return statistics.median(equities.values()) if equities else None


def classify_next_cards(equities, needed):
    """Split next cards into outs, helpers and danger cards.

    Each is measured against a typical next card. An out lifts your equity
    by OUT_JUMP and leaves you with at least the equity a call needs. A
    helper lifts it by HELP_JUMP but isn't an out. A danger card helps the
    other players: it drops your equity by DANGER_DROP, or by HELP_JUMP when
    that takes a call from paying to not.
    """
    base = next_card_baseline(equities)
    outs = {c for c, e in equities.items() if e >= needed and e >= base + OUT_JUMP}
    helps = {c for c, e in equities.items() if c not in outs and e >= base + HELP_JUMP}
    dangers = {c for c, e in equities.items()
               if e <= base - DANGER_DROP
               or (e <= base - HELP_JUMP and e < needed <= base)}
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
# Design tokens. Every colour comes from assets/tokens.css, a pinned copy of
# brignano/design's tokens.css, so this file never holds a hex of its own
# (DESIGN.md §12; tests/test_breakeven.py enforces it).
# --------------------------------------------------------------------------

def asset_path(name):
    """A file in assets/, next to this file or inside a PyInstaller bundle."""
    from pathlib import Path
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent)) / "assets" / name


def icon_path():
    """The window icon."""
    return asset_path("icon.png")


def parse_tokens(css):
    """`--name: value;` declarations -> {name: value}. The first one wins.

    The first declaration is the tool tier's, which is this app's tier; the
    marketing tier only reopens the type scale, never a colour.
    """
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    decls = {}
    for name, value in re.findall(r"--([\w-]+)\s*:\s*([^;]+);", css):
        decls.setdefault(name, " ".join(value.split()))
    return decls


def _call_args(value, fn):
    """`fn(a, b(c, d))` -> ['a', 'b(c, d)'], or None if `value` isn't a call to `fn`."""
    if not (value.startswith(fn + "(") and value.endswith(")")):
        return None
    args, depth, cur = [], 0, ""
    for ch in value[len(fn) + 1:-1]:
        if ch == "," and depth == 0:
            args.append(cur.strip())
            cur = ""
            continue
        depth += (ch == "(") - (ch == ")")
        cur += ch
    return args + [cur.strip()]


def mix(colour, ground, share):
    """`share` of `colour` over `ground`, as one opaque hex. Tk has no alpha."""
    a = [int(colour[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(ground[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x * share + y * (1 - share)):02x}" for x, y in zip(a, b))


def resolve_token(value, decls, dark, ground=None):
    """A token's value as a hex for one theme, or None if it isn't a colour.

    `color-mix(in srgb, <hex> N%, transparent)` washes are laid over `ground`.
    """
    value = value.strip()
    if args := _call_args(value, "light-dark"):
        return resolve_token(args[1] if dark else args[0], decls, dark, ground)
    if args := _call_args(value, "var"):
        name = args[0].removeprefix("--")
        return resolve_token(decls[name], decls, dark, ground) if name in decls else None
    if args := _call_args(value, "color-mix"):
        hue, _, pct = args[1].partition(" ")
        hue = resolve_token(hue, decls, dark, ground)
        if args[2] != "transparent" or not ground or not hue:
            return None
        return mix(hue, ground, float(pct.rstrip("%")) / 100)
    if re.fullmatch(r"#[0-9a-fA-F]{6}", value):
        return value.lower()
    if re.fullmatch(r"#[0-9a-fA-F]{3}", value):
        return "#" + "".join(c * 2 for c in value[1:].lower())
    return None


def load_theme(dark, css=None):
    """{token name: hex} for one theme. Washes are laid over --card."""
    decls = parse_tokens(css if css is not None else asset_path("tokens.css").read_text("utf-8"))
    card = resolve_token(decls["card"], decls, dark)
    theme = {}
    for name, value in decls.items():
        colour = resolve_token(value, decls, dark, card)
        if colour:
            theme[name] = colour
    return theme


def system_prefers_dark():
    """The OS theme, unless BREAKEVEN_THEME=light or dark says otherwise."""
    choice = os.environ.get("BREAKEVEN_THEME", "").strip().lower()
    if choice in ("light", "dark"):
        return choice == "dark"
    if sys.platform == "win32":
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                 r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
            return winreg.QueryValueEx(key, "AppsUseLightTheme")[0] == 0
        except OSError:
            return False
    if sys.platform == "darwin":
        try:
            out = subprocess.run(["defaults", "read", "-g", "AppleInterfaceStyle"],
                                 capture_output=True, text=True, timeout=2).stdout
            return out.strip() == "Dark"
        except (OSError, subprocess.SubprocessError):
            return False
    return False


# --------------------------------------------------------------------------
# GUI: plain Tk widgets drawn in the design system's colours, with
# canvas-drawn cards, so it looks the same on Windows and Mac instead of like
# a system dialog. Tool tier: compact, near-monochrome, colour only where it
# means something, and every coloured state also carries a symbol and a word.
# --------------------------------------------------------------------------

APP_NAME = "Breakeven"

# Seven card slots: two hole cards, then the board in dealing order.
SLOT_GROUPS = [("YOUR HAND", 0, 2), ("FLOP", 2, 5), ("TURN", 5, 6), ("RIVER", 6, 7)]
COMMON_OUTS = [("Flush draw", 9), ("Open-ended", 8), ("Gutshot", 4)]

# The symbol each state wears next to its colour.
OUT_GLYPH, HELP_GLYPH, DANGER_GLYPH = "✓", "+", "▼"


def _rounded_rect(cv, x1, y1, x2, y2, r, **kw):
    pts = [x1 + r, y1, x1 + r, y1, x2 - r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
           x2, y1 + r, x2, y2 - r, x2, y2 - r, x2, y2, x2 - r, y2, x2 - r, y2,
           x1 + r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y2 - r, x1, y1 + r,
           x1, y1 + r, x1, y1]
    return cv.create_polygon(pts, smooth=True, **kw)


def draw_mark(cv, x, y, w, h, fill, track, tick):
    """The Breakeven mark: an equity bar that clears the break-even tick.

    The same drawing as assets/icon.svg (scripts/make_icon.py).
    """
    bar_h = h * 0.3
    by = y + (h - bar_h) / 2
    cv.create_rectangle(x, by, x + w, by + bar_h, fill=track, outline="")
    cv.create_rectangle(x, by, x + w * 0.7, by + bar_h, fill=fill, outline="")
    tx = x + w * 0.55
    cv.create_rectangle(tx - h * 0.07, y, tx + h * 0.07, y + h, fill=tick, outline="")


def run_gui():
    import queue
    import threading
    import tkinter as tk
    import tkinter.font as tkfont

    T = load_theme(system_prefers_dark())
    root = tk.Tk()
    root.title(APP_NAME)
    try:
        root.icon = tk.PhotoImage(file=str(icon_path()))  # keep a reference so Tk keeps the image
        root.iconphoto(True, root.icon)
    except tk.TclError:
        pass  # No icon file (or no PNG support): the window still works.
    root.configure(bg=T["bg"])
    root.minsize(1, 1)

    # --sans (Geist) and --mono (IBM Plex Mono), falling back the way
    # tokens.css does to whatever the system has.
    families = set(tkfont.families())
    sans = next((f for f in ("Geist", "Inter", "Segoe UI", "SF Pro Text", "Helvetica Neue",
                             "DejaVu Sans") if f in families), "Helvetica")
    mono = next((f for f in ("IBM Plex Mono", "SF Mono", "Menlo", "Cascadia Mono", "Consolas",
                             "DejaVu Sans Mono") if f in families), "Courier")

    # Everything is drawn at a base size times `scale`, which follows the
    # window size. Fonts are shared objects, so resizing one updates every
    # widget and canvas text that uses it.
    scale = [1.0]
    fonts = {}

    def font(size, weight="normal", fixed=False):
        if (size, weight, fixed) not in fonts:
            fonts[size, weight, fixed] = tkfont.Font(family=mono if fixed else sans,
                                                     size=size, weight=weight)
        return fonts[size, weight, fixed]

    def px(v):
        return v * scale[0]

    def label(parent, text="", size=10, weight="normal", fg=T["ink-soft"], fixed=False, **kw):
        return tk.Label(parent, text=text, font=font(size, weight, fixed), fg=fg,
                        bg=parent["bg"], **kw)

    def eyebrow(parent, text):
        """A section label: mono, small, quiet."""
        return label(parent, text, 8, fg=T["slate"], fixed=True)

    def button(parent, text, command, size=10, primary=False):
        """A flat clickable button. Tk buttons ignore colours on macOS; labels don't.

        Secondary by default: the card with a control edge. `primary` is the
        cobalt fill, kept for the one main action.
        """
        if primary:
            rest, over, down, fg, edge = T["i"], T["i-hover"], T["i-pressed"], T["on-i"], T["i"]
        else:
            rest, over, down, fg, edge = (T["card"], T["surface-hover"], T["surface-active"],
                                          T["ink"], T["line-control"])
        w = tk.Label(parent, text=text, font=font(size, "bold"), fg=fg, bg=rest,
                     padx=10, pady=3, cursor="hand2", highlightthickness=1,
                     highlightbackground=edge)
        w.bind("<ButtonPress-1>", lambda _e: w.configure(bg=down))
        w.bind("<ButtonRelease-1>", lambda _e: (w.configure(bg=over), command()))
        w.bind("<Enter>", lambda _e: w.configure(bg=over))
        w.bind("<Leave>", lambda _e: w.configure(bg=rest))
        return w

    outer = tk.Frame(root, bg=T["bg"], padx=20, pady=16)
    outer.pack(expand=True)

    head = tk.Frame(outer, bg=T["bg"])
    head.pack(fill="x", pady=(0, 12))
    mark_cv = tk.Canvas(head, bg=T["bg"], highlightthickness=0)
    mark_cv.pack(side="left", padx=(0, 10))
    label(head, APP_NAME, 17, "bold", fg=T["ink"]).pack(side="left")
    label(head, "pot odds & equity", 10, fg=T["slate"]).pack(side="left", padx=10, pady=(6, 0))

    def draw_header_mark():
        w, h = px(30), px(18)
        mark_cv.configure(width=w, height=h)
        mark_cv.delete("all")
        draw_mark(mark_cv, 0, 0, w, h, T["mark"], T["line-strong"], T["ink"])

    panel = tk.Frame(outer, bg=T["card"], padx=20, pady=16,
                     highlightthickness=1, highlightbackground=T["line"])
    panel.pack(fill="x")

    # ---- Top row: amounts, opponents, pot odds ---------------------------
    top = tk.Frame(panel, bg=T["card"])
    top.pack(fill="x")
    fields = {}

    def entry(parent, var, width, size):
        return tk.Entry(parent, textvariable=var, width=width, font=font(size, "bold", True),
                        fg=T["ink"], bg=T["card"], insertbackground=T["ink"],
                        relief="flat", highlightthickness=2,
                        highlightbackground=T["line-control"], highlightcolor=T["i-ink"],
                        selectbackground=T["i-surface"], selectforeground=T["ink"])

    def amount(col, caption, key, default):
        box = tk.Frame(top, bg=T["card"])
        box.grid(row=0, column=col, sticky="w", padx=(0, 20))
        eyebrow(box, caption).pack(anchor="w")
        var = tk.StringVar(value=default)
        entry(box, var, 7, 15).pack(anchor="w", ipady=3, pady=(2, 0))
        fields[key] = var
        # Step the amount a big blind at a time.
        steps = tk.Frame(box, bg=T["card"])
        steps.pack(anchor="w", pady=(6, 0))
        button(steps, "−BB", lambda: bump(key, -1), 9).pack(side="left")
        button(steps, "+BB", lambda: bump(key, 1), 9).pack(side="left", padx=(4, 0))

    amount(0, "POT (INCL. THEIR BET)", "pot", "100")
    amount(1, "TO CALL", "call", "50")

    def stepper(parent, var, lo, hi):
        box = tk.Frame(parent, bg=T["card"])
        shown = label(box, str(var.get()), 15, "bold", fg=T["ink"], fixed=True, width=2)

        def step(d):
            var.set(min(hi, max(lo, var.get() + d)))
            shown.configure(text=str(var.get()))
            if var is outs:
                outs_manual[0], outs_auto[0] = True, False
            schedule()

        button(box, "−", lambda: step(-1), 12).pack(side="left")
        shown.pack(side="left", padx=4)
        button(box, "+", lambda: step(1), 12).pack(side="left")
        var.trace_add("write", lambda *_: shown.configure(text=str(var.get())))
        return box

    opps = tk.IntVar(value=1)
    # On the flop and turn, outs are counted from your cards unless you set
    # them yourself. A new spot (other cards or opponents) counts afresh.
    outs = tk.IntVar(value=0)
    outs_manual = [False]   # the user set the count for this spot
    outs_auto = [False]     # the count on show came from the cards
    spot = [None]
    obox = tk.Frame(top, bg=T["card"])
    obox.grid(row=0, column=2, sticky="nw")
    eyebrow(obox, "OPPONENTS").pack(anchor="w")
    stepper(obox, opps, 1, 9).pack(anchor="w", pady=(2, 0))

    odds_box = tk.Frame(top, bg=T["card"])
    odds_box.grid(row=0, column=3, sticky="ne")
    top.grid_columnconfigure(3, weight=1)
    eyebrow(odds_box, "POT ODDS").pack(anchor="e")
    odds_big = label(odds_box, "", 18, "bold", fg=T["ink"], fixed=True)
    odds_big.pack(anchor="e")
    odds_small = label(odds_box, "", 9, fg=T["slate"])
    odds_small.pack(anchor="e")

    # ---- Blinds -----------------------------------------------------------
    blinds_row = tk.Frame(panel, bg=T["card"])
    blinds_row.pack(fill="x", pady=(12, 0))
    eyebrow(blinds_row, "BLINDS").pack(side="left", padx=(0, 8))
    blinds = {"sb": tk.StringVar(value="1"), "bb": tk.StringVar(value="2")}
    entry(blinds_row, blinds["sb"], 5, 11).pack(side="left", ipady=1)
    label(blinds_row, "/", 12, "bold", fg=T["slate"]).pack(side="left", padx=4)
    entry(blinds_row, blinds["bb"], 5, 11).pack(side="left", ipady=1)
    # The one primary action on the screen.
    button(blinds_row, "New hand", lambda: new_hand(), primary=True).pack(side="left", padx=(12, 0))
    blinds_hint = label(blinds_row, "", 9, fg=T["slate"], anchor="e")
    blinds_hint.pack(side="right")

    def warn(widget, text):
        """An attention message: the symbol, the word, and the attention ink."""
        widget.configure(text=f"▲ {text}", fg=T["attention-ink"])

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

    slot_row = tk.Frame(panel, bg=T["card"])
    slot_row.pack(fill="x", pady=(16, 0))
    slot_cv = tk.Canvas(slot_row, bg=T["card"], highlightthickness=0)
    slot_cv.pack(side="left")
    button(slot_row, "Clear", lambda: clear_cards()).pack(side="right", anchor="s", pady=(0, 2))

    def draw_slots():
        slot_cv.delete("all")
        xs, _ = slot_xs()
        sw, sh, y0 = px(SW), px(SH), px(SLOT_TOP)
        for name, start, _end in SLOT_GROUPS:
            slot_cv.create_text(xs[start], px(6), text=name, anchor="w",
                                font=font(8, fixed=True), fill=T["slate"])
        for i, x0 in enumerate(xs):
            card = slots[i]
            current = i == active[0]
            if card is None:
                # The slot filled next wears the selection treatment.
                _rounded_rect(slot_cv, x0, y0, x0 + sw, y0 + sh, px(9), fill=T["bg"],
                              outline=T["i-ink"] if current else T["line-control"],
                              width=2 if current else 1, dash=() if current else (4, 3))
                if current:
                    slot_cv.create_text(x0 + sw / 2, y0 + sh / 2, text="+",
                                        font=font(18), fill=T["i-ink"])
            else:
                rank, suit = card_label(card)[:-1], card_label(card)[-1]
                _rounded_rect(slot_cv, x0, y0, x0 + sw, y0 + sh, px(9), fill=T["card"],
                              outline=T["i-ink"] if current else T["line-strong"],
                              width=2 if current else 1)
                slot_cv.create_text(x0 + px(8), y0 + px(6), text=rank, anchor="nw",
                                    font=font(13, "bold"), fill=T["ink"])
                slot_cv.create_text(x0 + sw / 2, y0 + sh / 2 + px(10), text=suit,
                                    font=font(24), fill=T["ink"])
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
    banner = tk.Canvas(panel, bg=T["card"], highlightthickness=0)
    banner.pack(pady=(14, 0), anchor="w")
    detail = label(panel, "", 10, justify="left", anchor="w")
    detail.pack(fill="x", pady=(6, 0))

    # Each verdict is a state: its wash, its edge, the ink for its word, and
    # the symbol that goes with the word.
    STATES = {
        "success": (T["success-surface"], T["success-line"], T["success-ink"], "✓"),
        "danger": (T["danger-surface"], T["danger-line"], T["danger-ink"], "✕"),
        "attention": (T["attention-surface"], T["attention-line"], T["attention-ink"], "▲"),
        "neutral": (T["bg"], T["line"], T["ink"], ""),
    }
    shown_banner = [None]

    def draw_banner(*args):
        shown_banner[0] = args
        paint_banner(*args)

    def paint_banner(word, state, headline, sub="", equity=None, needed=None):
        fill, edge, word_ink, glyph = STATES[state]
        banner.delete("all")
        bw, bh = px(BW), px(BH)
        _rounded_rect(banner, 1, 1, bw - 1, bh - 1, px(12), fill=fill, outline=edge)
        word = f"{glyph} {word}" if glyph else word
        banner.create_text(px(22), px(34), text=word, anchor="w", font=font(24, "bold"),
                           fill=word_ink)
        hx = max(px(170), px(22) + font(24, "bold").measure(word) + px(28))
        banner.create_text(hx, px(26), text=headline, anchor="w",
                           font=font(13, "bold"), fill=T["ink"])
        banner.create_text(hx, px(48), text=sub, anchor="w", font=font(10),
                           fill=T["ink-soft"])
        if equity is not None:
            # Equity bar, with a tick where the call breaks even.
            bx1, bx2, by, bt = px(22), bw - px(22), px(72), px(8)
            banner.create_rectangle(bx1, by, bx2, by + bt, fill=T["line-strong"], outline="")
            banner.create_rectangle(bx1, by, bx1 + (bx2 - bx1) * equity, by + bt,
                                    fill=T["ink-soft"], outline="")
            nx = bx1 + (bx2 - bx1) * needed
            banner.create_line(nx, by - px(5), nx, by + bt + px(5), fill=T["ink"],
                               width=px(3))

    def verdict(equity, needed, pot, call, basis):
        ev = call_ev(pot, call, equity)
        good = equity >= needed
        draw_banner("CALL" if good else "FOLD", "success" if good else "danger",
                    f"{equity:.1%} {basis}  ·  need {needed:.1%}",
                    f"EV of calling {ev:+.2f}" + ("" if good else "  ·  on pot odds alone"),
                    equity, needed)

    # ---- The deck ---------------------------------------------------------
    deck_head = tk.Frame(panel, bg=T["card"])
    deck_head.pack(fill="x", pady=(16, 6))
    deck_title = label(deck_head, "", 8, fg=T["slate"], fixed=True)
    deck_title.pack(side="left")
    # Fixed widths, in characters, so changing text never widens the window.
    deck_info = label(deck_head, "", 9, "bold", fg=T["ink"], width=30, anchor="e")
    deck_info.pack(side="right")
    deck_cv = tk.Canvas(panel, bg=T["card"], highlightthickness=0, cursor="hand2")
    deck_cv.pack(anchor="w")
    hover = [None]
    # Next-card highlights: {"eq": {card: equity}, "outs": set, "helps": set,
    # "dangers": set}.
    marks = {"eq": {}, "outs": set(), "helps": set(), "dangers": set()}

    def set_marks(eq=None, outs_=(), helps=(), dangers=()):
        marks.update(eq=eq or {}, outs=set(outs_), helps=set(helps), dangers=set(dangers))
        if marks["eq"]:
            deck_title.configure(text=f"DECK   {OUT_GLYPH} {len(marks['outs'])} outs  ·  "
                                      f"{HELP_GLYPH} {len(marks['helps'])} help  ·  "
                                      f"{DANGER_GLYPH} {len(marks['dangers'])} danger")
        else:
            deck_title.configure(text="DECK   click a card to fill the outlined slot")
        draw_deck()
        show_hover_info()

    def show_hover_info():
        c = hover[0]
        if c is not None and c in marks["eq"]:
            deck_info.configure(text=f"{card_label(c)}: {marks['eq'][c]:.0%} to win "
                                     f"(typical {next_card_baseline(marks['eq']):.0%})")
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
                fg, glyph, glyph_ink, width = T["ink"], "", "", 1
                if card in used:
                    # Disabled is neutral, never hued.
                    fill, fg, outline = T["bg"], T["i-disabled-ink"], T["line"]
                elif card in marks["outs"]:
                    fill, outline, width = T["success-surface"], T["success"], 2
                    glyph, glyph_ink = OUT_GLYPH, T["success-ink"]
                elif card in marks["helps"]:
                    fill, outline = T["card"], T["success-line"]
                    glyph, glyph_ink = HELP_GLYPH, T["success-ink"]
                elif card in marks["dangers"]:
                    fill, outline, width = T["danger-surface"], T["danger"], 2
                    glyph, glyph_ink = DANGER_GLYPH, T["danger-ink"]
                else:
                    fill, outline = T["card"], T["line-strong"]
                if hover[0] == card and card not in used:
                    outline, width = T["i-ink"], 2
                _rounded_rect(deck_cv, x0, y0, x0 + dw, y0 + dh, px(7), fill=fill,
                              outline=outline, width=width)
                deck_cv.create_text(x0 + dw / 2, y0 + px(16), text=card_label(card)[:-1],
                                    font=font(12, "bold"), fill=fg)
                deck_cv.create_text(x0 + dw / 2, y0 + px(35), text=card_label(card)[-1],
                                    font=font(14), fill=fg)
                if glyph:
                    deck_cv.create_text(x0 + dw - px(4), y0 + dh - px(2), text=glyph, anchor="se",
                                        font=font(8, "bold"), fill=glyph_ink)

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
    outs_row = tk.Frame(panel, bg=T["card"])
    outs_row.pack(fill="x", pady=(14, 0))
    eyebrow(outs_row, "OUTS").pack(side="left", padx=(0, 8))
    stepper(outs_row, outs, 0, 20).pack(side="left")

    def preset(n):
        outs.set(n)
        outs_manual[0], outs_auto[0] = True, False
        schedule()

    for name, n in COMMON_OUTS:
        button(outs_row, f"{name} · {n}", lambda n=n: preset(n)).pack(side="left", padx=(8, 0))
    outs_hint = label(outs_row, "optional", 9, fg=T["slate"], width=15, anchor="e")
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

    def num(key, name, source=fields):
        raw = source[key].get().strip().replace("$", "").replace(",", "")
        if not raw:
            raise ValueError(f"Fill in the {name}.")
        try:
            return float(raw)
        except ValueError:
            raise ValueError(f"The {name} should be a number.") from None

    def blind(key):
        """A blind as a number, or None while it isn't a positive one."""
        try:
            value = num(key, "blind", blinds)
        except ValueError:
            return None
        return value if value > 0 else None

    def bump(key, times):
        bb = blind("bb")
        if bb is None:
            warn(blinds_hint, "Set the big blind first.")
            return
        try:
            current = num(key, "")
        except ValueError:
            current = 0.0
        fields[key].set(format_amount(step_amount(current, bb, times)))

    def new_hand():
        """Preflop with the blinds posted: the pot holds both, and you face the big blind."""
        sb, bb = blind("sb"), blind("bb")
        if sb is None or bb is None:
            warn(blinds_hint, "Set both blinds first.")
            return
        fields["pot"].set(format_amount(sb + bb))
        fields["call"].set(format_amount(bb))
        clear_cards()

    # Results update as you go. Each run gets a number, so a slow simulation
    # that finishes after a newer one started is thrown away.
    run_id = [0]
    pending = [None]

    # Simulations run on a worker thread, which hands its results back here
    # rather than touching Tk itself: not every Tk takes calls from threads.
    results = queue.Queue()

    def take_results():
        while not results.empty():
            results.get()()
        root.after(50, take_results)

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
            draw_banner("CHECK", "attention", str(e), "Type the pot and the bet you face.")
            return

        needed = pot_odds(pot, call)
        odds_big.configure(text=f"{pot / call:.2f} : 1" if call else "free")
        odds_small.configure(text=f"need {needed:.1%} equity")
        bb = blind("bb")
        blinds_hint.configure(
            text=(f"pot {format_amount(pot / bb)} BB  ·  call {format_amount(call / bb)} BB"
                  if bb else "Type the blinds to step by big blinds."), fg=T["slate"])

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
                draw_banner("CHECK", "success", "Nothing to call",
                            "It costs nothing to see more cards.")
            elif outs_hit is not None:
                verdict(outs_hit, needed, pot, call, "to hit next card")
            else:
                draw_banner("NEED", "neutral", f"{needed:.1%} equity to call",
                            "Pick your cards or set your outs to get a verdict.",
                            0.0, needed)

        if not can_sim:
            fallback()
            return

        n_opps = opps.get()
        draw_banner("…", "neutral", "Simulating",
                    f"5,000 hands against {n_opps} random hand{'s' * (n_opps > 1)}")

        def work():
            try:
                eq = simulate_equity(hole, board, n_opps)
            except ValueError as e:
                results.put(lambda: run_id[0] == me and draw_banner("CHECK", "attention", str(e)))
                return

            def done():
                if run_id[0] != me:
                    return
                if call:
                    verdict(eq, needed, pot, call,
                            f"to win vs {n_opps} hand{'s' * (n_opps > 1)}")
                else:
                    draw_banner("CHECK", "success", f"{eq:.1%} to win",
                                "Nothing to call.", eq, 0.0)
            results.put(done)
            if not auto:
                return

            # Then try every possible next card, to light up the outs.
            per_card = next_card_equities(hole, board, n_opps, stop=lambda: run_id[0] != me)

            def marked():
                if run_id[0] != me or not per_card:
                    return
                outs_, helps, dangers = classify_next_cards(per_card, needed)
                set_marks(per_card, outs_, helps, dangers)
                if not outs_manual[0]:
                    outs.set(len(outs_))
                    outs_auto[0] = True
                    show_notes(len(outs_))
                    outs_hint.configure(text="from your cards")
            results.put(marked)

        threading.Thread(target=work, daemon=True).start()

    for var in (*fields.values(), *blinds.values()):
        var.trace_add("write", lambda *_: schedule())

    def apply_scale():
        for (size, _weight, _fixed), f in fonts.items():
            f.configure(size=max(1, round(size * scale[0])))
        draw_header_mark()
        slot_cv.configure(width=slot_xs()[1], height=px(SLOT_TOP + SH + 4))
        banner.configure(width=px(BW), height=px(BH))
        detail.configure(wraplength=px(BW))
        deck_cv.configure(width=px(13 * (DW + DG)), height=px(4 * (DH + DG)))
        draw_slots()
        draw_deck()
        if shown_banner[0]:
            paint_banner(*shown_banner[0])

    # Scale everything to fit the window. The window's natural size is
    # fixed padding plus content that grows with the scale, so measure it
    # at two scales and solve for both parts.
    MIN_SCALE, MAX_SCALE = 0.75, 4.0
    parts = [None]
    resize_pending = [None]

    def natural_size(s):
        scale[0] = s
        apply_scale()
        root.update_idletasks()
        return root.winfo_reqwidth(), root.winfo_reqheight()

    def fit(width, height):
        (fw, fh), (gw, gh) = parts[0]
        s = min((width - fw - 16) / gw, (height - fh - 16) / gh)
        return max(MIN_SCALE, min(MAX_SCALE, s))

    def on_resize(event):
        if event.widget is not root or parts[0] is None:
            return
        if resize_pending[0] is not None:
            root.after_cancel(resize_pending[0])
        resize_pending[0] = root.after(40, rescale)

    def rescale():
        resize_pending[0] = None
        new = fit(root.winfo_width(), root.winfo_height())
        if abs(new - scale[0]) > 0.02:
            scale[0] = new
            apply_scale()

    take_results()

    # Measure hidden, so the window doesn't flash at the test sizes.
    root.withdraw()
    apply_scale()
    calculate()
    w1, h1 = natural_size(1.0)
    w2, h2 = natural_size(2.0)
    grow = (w2 - w1, h2 - h1)
    parts[0] = ((w1 - grow[0], h1 - grow[1]), grow)

    # Open at the base size, or smaller if that wouldn't fit on the screen
    # (leaving room for the taskbar and title bar).
    root.minsize(*natural_size(MIN_SCALE))
    start = min(1.0, fit(root.winfo_screenwidth() - 40, root.winfo_screenheight() - 120))
    w, h = natural_size(start)
    root.geometry(f"{w}x{h}+20+20")
    root.resizable(True, True)
    root.deiconify()
    root.bind("<Configure>", on_resize)
    root.mainloop()


if __name__ == "__main__":
    run_gui()
