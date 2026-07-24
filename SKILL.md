---
name: macd
description: Analyze MACD from OHLCV data or charts using a conservative, multi-factor workflow that separates observation from inference and avoids standalone buy/sell calls.
---

# MACD Analysis

Use this skill when the user asks whether a stock, ETF, index, crypto asset, or other traded instrument looks strong or weak based on MACD, wants a MACD chart explained, or provides OHLCV data for short-term trend analysis.

The goal is **decision support**, not prediction. MACD is a lagging transformation of historical prices. Never present a crossover, divergence, or histogram change as proof that price must rise or fall.

## Required Inputs

Resolve as many of these as possible before analysis:

- instrument and market, because tickers can be ambiguous
- timeframe of each bar, such as daily, 60-minute, or 5-minute
- analysis horizon, such as intraday, several days, or several weeks
- data source and "as of" timestamp
- OHLCV data, indicator values, or a readable chart

Do not invent missing prices or indicator values. When only a screenshot is available, label numerical conclusions as approximate and do not claim an exact crossover time unless it is visible.

## Default Parameters

Use `MACD(12, 26, 9)` unless the user supplies different parameters:

- MACD line = fast EMA minus slow EMA
- signal line = EMA of the MACD line
- histogram = MACD line minus signal line

State any non-default parameters. Do not tune parameters to make a preferred conclusion look stronger.

## Deterministic CSV Calculation

When a CSV is available, run:

```bash
python3 <skill-dir>/scripts/analyze_macd.py data.csv --pretty
```

The CSV must contain `close`; `date`/`timestamp` and `volume` are optional. For a human-readable report:

```bash
python3 <skill-dir>/scripts/analyze_macd.py data.csv --format markdown
```

The script uses SMA-seeded EMAs and intentionally fetches no live market data. Different charting platforms may differ slightly because of data adjustment, session boundaries, warm-up rules, or EMA initialization.

## Analysis Workflow

1. **Validate scope and freshness**
   - Identify instrument, market, timeframe, parameters, source, and as-of time.
   - Warn when data is stale, incomplete, unadjusted, or has too little warm-up history. Prefer at least `slow + signal - 1` bars; more is better.

2. **Describe price structure first**
   - Is price trending, ranging, breaking out, breaking down, or sitting near a known support/resistance area?
   - MACD signals inside a range deserve less confidence because whipsaws are common.

3. **Read the MACD state**
   - MACD above/below the signal line: current directional momentum relation.
   - MACD above/below zero: whether the fast EMA is above/below the slow EMA.
   - Histogram expanding/contracting: acceleration or deceleration of the MACD-signal spread, not direct proof of future price direction.
   - Recent crossover age: a fresh cross and an old cross are not equivalent.

4. **Seek confirmation**
   - price follow-through after a cross
   - breakout/breakdown relative to recent structure
   - volume expansion when volume is meaningful and available
   - agreement with a higher timeframe

5. **Check conflicts and failure modes**
   - price and MACD disagree
   - low-volume move
   - repeated crosses around zero
   - news-driven gap or exceptional volatility
   - insufficient bars or unclear chart scale

6. **Build scenarios, not commands**
   - bullish evidence and what would strengthen it
   - neutral/range evidence
   - bearish evidence and what would strengthen it
   - invalidation levels or observable conditions when available

## Divergence Rules

Treat divergence as a secondary observation and require clear swing points:

- bullish divergence: price makes a lower swing low while MACD makes a higher swing low
- bearish divergence: price makes a higher swing high while MACD makes a lower swing high

Do not call divergence from tiny adjacent fluctuations. State which two swing points are being compared. Divergence can persist and is not a timing signal by itself.

## Multi-Timeframe Rules

Keep each timeframe separate. A practical hierarchy is:

- higher timeframe: regime and major structure
- execution timeframe: setup and trigger
- lower timeframe: optional entry refinement, with the highest noise

Do not merge daily and intraday MACD values into one unnamed conclusion. When signals conflict, say so and reduce confidence.

## Output Format

Use this structure:

### Scope
Instrument, market, timeframe, parameters, source, and as-of timestamp.

### Observations
Exact or approximate facts from price, MACD, signal line, histogram, zero axis, volume, and relevant structure.

### Interpretation
Explain what the observations support and what they do not establish.

### Scenario Matrix

| Scenario | Evidence required | What weakens it |
| --- | --- | --- |
| Bullish continuation | Price follow-through, MACD holds above signal, improving histogram, supportive volume/structure | Failed breakout, histogram deterioration, cross back below signal |
| Range/unclear | Repeated crosses, flat zero-axis behavior, no price follow-through | Clean structural break with confirmation |
| Bearish continuation | Price breakdown, MACD below signal/zero, weakening histogram, supportive volume/structure | Reclaim of structure, improving histogram, cross back above signal |

### Risk and Limitations
Mention lag, whipsaw risk, data limitations, event risk, and that the analysis is not individualized investment advice.

## Language Rules

- Prefer: "supports", "suggests", "is consistent with", "would be confirmed by".
- Avoid: "will rise", "must fall", "guaranteed", "sure win", or an unqualified "buy/sell now".
- Separate observed facts from inference.
- If the user asks for a direct trade, provide conditional scenarios and risk controls rather than certainty.

## Boundaries

- Do not execute trades or imply access to the user's brokerage account.
- Do not fabricate live data.
- Do not use MACD alone to size a position.
- Do not backtest only the winning examples or silently change parameters.
- For material financial decisions, encourage independent verification and consideration of the user's objectives, horizon, liquidity needs, and risk tolerance.
