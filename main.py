"""Long-only trend bot for cbBTC (CBBTC) on the bars-replay/v1 harness.

Strategy, in one paragraph: stay long while the slow trend is up, stay in
cash while it is down, never short. The trend is the 30-bar average close
against the 120-bar average close, both integer sums so no float ever
decides an order, with a 15 bps deadband: the averages only count as
crossed when they differ by more than the band, because on a flat market
they sit within noise of each other and a bare cross flips on every
wiggle. A buy needs three straight bars of fast-above-slow by the band
the close above the fast average and the 60-bar return positive, which
keeps 1-minute noise from whipsawing the bot (the fast EMA-cross baseline
lost $114.83 on this dev window with 76 trades). A sell fires when the
fast average stays below the slow one for three straight bars, or at once
when the close drops 3% under the entry or under the peak since entry.
A flip only cuts a position that is under water; a winning position rides
on under the trailing stop, so a step down inside an uptrend does not
whipsaw it out and back in higher. Position is all-in
cash on a buy and the whole holding on a sell; at most one position, at
most one order per reply. Deterministic: only bar closes drive decisions.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))

import makefun_bars

SYMBOL = "CBBTC"
FAST = 30
SLOW = 120
CONFIRM = 3
MAX_SLIP = 200
STOP_NUM = 970
STOP_DEN = 1000
EXIT_CONFIRM = 3

closes = []
confirm = 0
down_confirm = 0
holding = False
entry_close = 0
peak_close = 0


def _sma_sum(n):
    total = 0
    for c in closes[-n:]:
        total += c
    return total


def _trend_up():
    # Fast above slow by more than the deadband (15 bps): when the two
    # averages sit within noise of each other on a flat market, a bare
    # cross flips on every wiggle, so the band holds the current state.
    fast_sum = _sma_sum(FAST)
    slow_sum = _sma_sum(SLOW)
    return fast_sum * SLOW * 10000 > slow_sum * FAST * 10015


def _trend_down():
    fast_sum = _sma_sum(FAST)
    slow_sum = _sma_sum(SLOW)
    return fast_sum * SLOW * 10000 < slow_sum * FAST * 9985


def _close_above_fast():
    return closes[-1] * FAST > _sma_sum(FAST)


def _hour_up():
    return len(closes) > 60 and closes[-1] > closes[-61]


def on_batch(state, batch):
    global confirm, down_confirm, holding, entry_close, peak_close
    if state.warming_up:
        return []
    close = state.close(SYMBOL)
    if close is None:
        return []
    closes.append(close)
    if holding and close > peak_close:
        peak_close = close
    if len(closes) < SLOW:
        return []
    in_pos = SYMBOL in state.positions
    if in_pos:
        stopped = close * STOP_DEN < peak_close * STOP_NUM
        under_entry = close * STOP_DEN < entry_close * STOP_NUM
        if _trend_down():
            down_confirm += 1
        elif _trend_up():
            down_confirm = 0
        # A trend flip cuts a LOSING position at once; a winning one is
        # left to run under the trailing stop, because a step down in an
        # uptrend flips the averages yet the position is still ahead.
        losing = close < entry_close
        if stopped or under_entry or (down_confirm >= EXIT_CONFIRM and losing):
            holding = False
            entry_close = 0
            peak_close = 0
            confirm = 0
            down_confirm = 0
            qty = state.positions[SYMBOL].qty
            return [{"side": "sell", "symbol": SYMBOL, "qty": qty,
                     "max_slippage_bps": MAX_SLIP}]
        return []
    if holding:
        return []
    if _trend_up() and _close_above_fast() and _hour_up():
        confirm += 1
    else:
        confirm = 0
    if confirm < CONFIRM:
        return []
    confirm = 0
    holding = True
    entry_close = close
    peak_close = close
    return [{"side": "buy", "symbol": SYMBOL,
             "notional_quote_units": state.cash,
             "max_slippage_bps": MAX_SLIP}]


makefun_bars.run(on_batch)
