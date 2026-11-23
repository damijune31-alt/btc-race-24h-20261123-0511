# BTC Race Bot — Long-Only Trend Follower

[![make.fun](https://make.fun/badge/btc-race-24h-20261123-0511.svg)](https://make.fun/bounty/btc-race-24h-20261123-0511)
[![rank](https://make.fun/badge/btc-race-24h-20261123-0511/damijune31-alt/btc-race-24h-20261123-0511/rank.svg)](https://make.fun/bounty/btc-race-24h-20261123-0511)
[![reward](https://make.fun/badge/btc-race-24h-20261123-0511/damijune31-alt/btc-race-24h-20261123-0511/reward.svg)](https://make.fun/bounty/btc-race-24h-20261123-0511)

A long-only trend-following bot for the [make.fun BTC race bounty](https://make.fun/bounty/btc-race-24h-20261123-0511): it trades cbBTC (CBBTC) minute by minute on the bars-replay/v1 harness, starting from $1,000. It never shorts.

## Strategy

- **Trend:** 30-bar vs 120-bar average close, integer math only, with a 15 bps deadband — the averages only count as crossed when they differ by more than the band, because on a flat market they sit within noise and a bare cross flips on every wiggle.
- **Entry:** three straight bars of fast-above-slow by the band, close above the fast average, 60-bar return positive. All-in cash.
- **Exit:** a trend flip cuts a position that is under water; a winning position rides on under a 3% trailing stop (also 3% under entry). Sells the whole holding, at most one order per reply.
- **Deterministic:** only bar closes drive decisions — no network, no wall clock, no files outside the repo, standard library only (plus the kit's `vendor/makefun_bars.py` shim, copied byte-identical).

## Local dev-window replay (frozen 24h window from the kit)

Measured with a local replay driver implementing the kit's exact integer fill math (fee 4 bps, slippage 2 bps, constant-product impact vs the bar's open depth). The driver was calibrated against `grade-local`: buy-and-hold reproduces the server's local grade exactly (+$32.1673, 1 trade, 1.98% max drawdown).

| Bot | Net PnL | Trades | Max drawdown |
| --- | --- | --- | --- |
| This bot (v4) | **+$30.36** | 1 | 1.98% |
| Buy-and-hold | +$32.17 | 1 | 1.98% |
| Momentum baseline | +$34.94 | 1 | 1.98% |
| EMA-cross baseline | −$114.83 | 76 | 11.65% |

Dev gate: net PnL > $0 — passed with margin. Two runs of the replay produce identical results (deterministic).

## Files

- `main.py` — the bot (Python 3.13, stdlib only)
- `vendor/makefun_bars.py` — the kit's protocol shim, byte-identical copy
