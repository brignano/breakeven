import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from breakeven import (call_ev, card_label, format_amount, hand_rank, icon_path, next_empty_slot,
                      outs_probability, parse_cards as p, pot_odds, simulate_equity,
                      step_amount)


def test_hand_rank():
    assert hand_rank(p("As Ks Qs Js Ts 2d 3c"))[0] == 8          # straight flush
    assert hand_rank(p("Ah 2h 3h 4h 5h")) == (8, 3)              # steel wheel
    assert hand_rank(p("Ah 2d 3c 4s 5h Kd Kc")) == (4, 3)        # wheel beats a pair
    assert hand_rank(p("Kh Kd Kc 2s 2h 2d 9c")) == (6, 11, 0)    # two trips = full house
    assert hand_rank(p("7h 7d 7c 7s 2h 3d 9c")) == (7, 5, 7)     # quads, best kicker
    assert hand_rank(p("9h 9d 4c 4s 2h 2d Ac")) == (2, 7, 2, 12) # three pairs, ace kicker
    assert hand_rank(p("Ah Kh 2h 7h 9h Qh 3c"))[:3] == (5, 12, 11)
    assert hand_rank(p("10♥ J♥ Q♥ K♥ A♥"))[0] == 8


def test_odds():
    assert abs(pot_odds(100, 50) - 1 / 3) < 1e-9
    assert pot_odds(100, 0) == 0
    assert abs(call_ev(100, 50, 0.5) - 25) < 1e-9
    nxt, river = outs_probability(9, 3)
    assert abs(nxt - 9 / 47) < 1e-9 and abs(river - 0.3497) < 1e-3
    assert outs_probability(9, 4)[1] is None
    assert outs_probability(9, 0) == (None, None)


def test_parse_errors():
    for bad in ("Ah Ah", "Xh", "A"):
        try:
            p(bad)
        except ValueError:
            continue
        raise AssertionError(bad)


def test_equity_matches_known_values():
    rng = random.Random(1)
    assert abs(simulate_equity(p("Ah Ad"), [], 1, 20000, rng) - 0.852) < 0.01
    assert abs(simulate_equity(p("7h 2d"), [], 1, 20000, rng) - 0.346) < 0.01


def test_card_picker_helpers():
    assert [card_label(c) for c in p("Ah Td 2c Ks")] == ["A♥", "10♦", "2♣", "K♠"]
    assert next_empty_slot([1, None, None], 0) == 1
    assert next_empty_slot([None, 1, 2], 2) == 0                 # wraps round
    assert next_empty_slot([1, 2, 3], 1) == 1                    # all full: stay


def test_next_card_highlights():
    from breakeven import classify_next_cards, next_card_equities
    rng = random.Random(3)
    hole, board = p("Ah Kh"), p("Qh Jh 2c")
    eq = next_card_equities(hole, board, 1, 300, rng)
    assert len(eq) == 47 and not set(eq) & set(hole + board)
    assert eq[p("Th")[0]] == 1.0                                  # royal flush
    outs, helps, dangers = classify_next_cards(eq, 1 / 3)
    hearts = {c for c in p("2h 3h 4h 5h 6h 7h 8h 9h Th")}
    assert hearts <= outs                                         # every flush card
    assert not outs & helps and not dangers & (outs | helps)
    assert next_card_equities(hole, [], 1) == {}                  # nothing preflop
    assert next_card_equities(hole, board, 1, stop=lambda: True) == {}


def test_danger_cards():
    from breakeven import classify_next_cards, next_card_equities
    rng = random.Random(5)
    # A set of kings on a spade-heavy turn: any spade makes a flush for a
    # hand holding one, a ten makes broadway for a hand holding an ace, and
    # an ace or a nine makes a straight for a hand holding a ten.
    hole, board = p("Kd Kc"), p("Ks Qs Js 2h")
    eq = next_card_equities(hole, board, 1, 600, rng)
    outs, helps, dangers = classify_next_cards(eq, 1 / 3)
    sure = set(p("As Ts 9s 8s 7s 6s 5s 4s 3s Th Td Tc"))
    assert sure <= dangers <= sure | set(p("Ah Ad Ac 9h 9d 9c"))
    assert not dangers & (outs | helps)
    # A drop past the call line counts at a smaller step. The typical card
    # (the median) is 0.50 here.
    _o, _h, dz = classify_next_cards({0: 0.48, 1: 0.44, 2: 0.38, 3: 0.50, 4: 0.50,
                                      5: 0.52, 6: 0.55}, 0.45)
    assert dz == {1, 2}


def test_blanks_are_not_danger_cards():
    from breakeven import classify_next_cards, next_card_equities
    # A weak draw on the flop: a blank turn costs one of two chances to hit,
    # but that is no reason to flag it.
    rng = random.Random(1)
    hole, board = p("7s 6s"), p("Ah Kh Qh")
    eq = next_card_equities(hole, board, 1, 300, rng)
    outs, _helps, dangers = classify_next_cards(eq, 1 / 3)
    assert not dangers
    assert set(p("7d 7c 6d 6c")) <= outs


def test_blind_steps():
    assert step_amount(100, 2, 1) == 102
    assert step_amount(3, 2, -1) == 1
    assert step_amount(1, 2, -1) == 0          # never below zero
    assert format_amount(step_amount(0.5, 0.25, 3)) == "1.25"
    assert format_amount(12.0) == "12"
    assert format_amount(0.1 + 0.2) == "0.3"


def test_icon_ships_with_the_app():
    # The window loads this PNG; the build workflow bundles it next to the app.
    assert icon_path().is_file()
    assert icon_path().read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"


# Every token the window paints with, in both themes.
UI_TOKENS = ("bg", "card", "ink", "ink-soft", "slate", "line", "line-strong", "line-control",
             "surface-hover", "surface-active", "i", "i-ink", "i-hover", "i-pressed", "on-i",
             "i-surface", "i-disabled-ink", "success", "success-ink", "success-surface",
             "success-line", "danger", "danger-ink", "danger-surface", "danger-line",
             "attention-ink", "attention-surface", "attention-line", "mark", "n-700", "on-dark")


def test_design_tokens_resolve_in_both_themes():
    import re
    from breakeven import asset_path, load_theme
    assert asset_path("tokens.css").is_file()
    light, dark = load_theme(False), load_theme(True)
    for name in UI_TOKENS:
        assert re.fullmatch(r"#[0-9a-f]{6}", light[name]), name
        assert re.fullmatch(r"#[0-9a-f]{6}", dark[name]), name
    assert light["ink"] != dark["ink"] and light["bg"] != dark["bg"]


def test_token_parsing():
    from breakeven import load_theme, mix
    css = """/* --ignored: #000000; */
    :root { --a: light-dark(#ffffff, #000); --b: var(--a);
            --card: light-dark(#ffffff, #000000);
            --wash: light-dark(color-mix(in srgb, #ff0000 50%, transparent), #00ff00); }
    .tier-marketing { --a: #123456; }"""
    light, dark = load_theme(False, css), load_theme(True, css)
    assert light["a"] == light["b"] == "#ffffff" and dark["b"] == "#000000"
    assert "ignored" not in light
    assert light["wash"] == mix("#ff0000", "#ffffff", 0.5) == "#ff8080"
    assert dark["wash"] == "#00ff00"


def test_no_hex_outside_the_tokens():
    # DESIGN.md §12: a literal colour survives a theme change silently.
    import re
    from breakeven import asset_path
    source = asset_path("tokens.css").parent.parent / "breakeven.py"
    assert not re.findall(r"#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b", source.read_text("utf-8"))


# Two PokerStars hands as they appear in a hand history file: a 6-max cash
# hand where you call, raise and call an all-in, then a tournament hand with
# antes where you fold.
HISTORY = """﻿PokerStars Hand #254343322345:  Hold'em No Limit ($0.01/$0.02 USD) - 2025/01/01 12:00:00 ET
Table 'Alcyone II' 6-max Seat #3 is the button
Seat 1: player1 ($2.00 in chips)
Seat 2: Hero ($2.13 in chips)
Seat 3: btn guy ($1.00 in chips)
Seat 4: sb player ($2.00 in chips)
Seat 5: bbplayer ($2.00 in chips)
Seat 6: player6 ($2.00 in chips) is sitting out
sb player: posts small blind $0.01
bbplayer: posts big blind $0.02
*** HOLE CARDS ***
Dealt to Hero [Ah Kh]
player1: raises $0.04 to $0.06
Hero: calls $0.06
btn guy: folds
sb player: folds
bbplayer: calls $0.04
*** FLOP *** [Qh Jh 2c]
bbplayer: checks
player1: bets $0.10
Hero: raises $0.20 to $0.30
bbplayer: folds
player1: calls $0.20
*** TURN *** [Qh Jh 2c] [3s]
player1: bets $1.64 and is all-in
Hero: calls $1.64
*** RIVER *** [Qh Jh 2c 3s] [Th]
*** SHOW DOWN ***
Hero: shows [Ah Kh] (a royal flush)
player1: shows [Qd Qc] (three of a kind, Queens)
Hero collected $3.95 from pot
*** SUMMARY ***
Total pot $4.07 | Rake $0.12
Board [Qh Jh 2c 3s Th]
Seat 2: Hero showed [Ah Kh] and won ($3.95) with a royal flush



PokerStars Hand #254343322400: Tournament #3700000000, $1.00+$0.10 USD Hold'em No Limit - Level III (25/50) - 2025/01/01 12:30:00 ET
Table '3700000000 1' 9-max Seat #1 is the button
Seat 1: alice (1500 in chips)
Seat 2: Hero (2,000 in chips)
Seat 3: bob (1500 in chips)
alice: posts the ante 5
Hero: posts the ante 5
bob: posts the ante 5
Hero: posts small blind 25
bob: posts big blind 50
*** HOLE CARDS ***
Dealt to Hero [7c 2d]
alice: raises 100 to 150
Hero: folds
bob: folds
Uncalled bet (100) returned to alice
alice collected 140 from pot
*** SUMMARY ***
Total pot 140 | Rake 0
Seat 1: alice (button) collected (140)

PokerStars Hand #254343322500: Pot Limit Omaha ($0.01/$0.02 USD) - 2025/01/01 13:00:00 ET
"""


def test_hand_history_cash_hand():
    from breakeven import parse_hand_histories
    hands = parse_hand_histories(HISTORY)
    assert [h.hand_id for h in hands] == ["254343322345", "254343322400"]   # Omaha skipped
    hand = hands[0]
    assert hand.hero == "Hero" and hand.hole == p("Ah Kh")
    assert (hand.small_blind, hand.big_blind) == (0.01, 0.02)
    assert hand.net == 1.95 and hand.currency == "$"   # won 3.95, put in 2.00
    pre, flop, turn = hand.decisions
    # Preflop: blinds and the raise are in, you face 0.06; four others dealt in.
    assert (pre.street, pre.pot, pre.to_call, pre.opponents, pre.action) == \
        ("Preflop", 0.09, 0.06, 4, "calls")
    assert pre.board == []
    # Flop: you raise against a 0.10 bet into 0.19; the bettor and the big blind are left.
    assert (flop.street, flop.pot, flop.to_call, flop.opponents, flop.action) == \
        ("Flop", 0.29, 0.10, 2, "raises")
    assert flop.board == p("Qh Jh 2c")
    # Turn: the all-in bet, one opponent left.
    assert (turn.pot, turn.to_call, turn.opponents, turn.board) == (2.43, 1.64, 1, p("Qh Jh 2c 3s"))


def test_hand_history_tournament_hand():
    from breakeven import parse_hand_histories
    hand = parse_hand_histories(HISTORY)[1]
    assert hand.hole == p("7c 2d") and (hand.small_blind, hand.big_blind) == (25, 50)
    assert hand.net == -30 and hand.currency == ""     # ante and small blind
    (fold,) = hand.decisions
    # Antes (dead) are in the pot but not in what you need to match.
    assert (fold.pot, fold.to_call, fold.opponents, fold.action) == (240, 125, 2, "folds")


def test_grades():
    from breakeven import grade
    assert grade("calls", 0.40, 0.33) == ("success", "✓ call paid")
    assert grade("calls", 0.20, 0.33)[0] == "attention"            # cards to come
    assert grade("calls", 0.20, 0.33, river=True) == ("danger", "✕ called short")
    assert grade("folds", 0.20, 0.33) == ("success", "✓ good fold")
    assert grade("folds", 0.40, 0.33)[0] == "attention"
    assert grade("raises", 0.9, 0.1)[0] == "neutral"
