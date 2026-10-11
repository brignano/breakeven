import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pot_odds import (call_ev, hand_rank, outs_probability, parse_cards as p,
                      pot_odds, simulate_equity)


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
