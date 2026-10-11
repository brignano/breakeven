import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pot_odds import (call_ev, card_label, hand_rank, next_empty_slot, outs_probability,
                      parse_cards as p, pot_odds, simulate_equity)


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
    from pot_odds import classify_next_cards, next_card_equities
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
    from pot_odds import classify_next_cards, next_card_equities
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
    from pot_odds import classify_next_cards, next_card_equities
    # A weak draw on the flop: a blank turn costs one of two chances to hit,
    # but that is no reason to flag it.
    rng = random.Random(1)
    hole, board = p("7s 6s"), p("Ah Kh Qh")
    eq = next_card_equities(hole, board, 1, 300, rng)
    outs, _helps, dangers = classify_next_cards(eq, 1 / 3)
    assert not dangers
    assert set(p("7d 7c 6d 6c")) <= outs
