# MACD Interpretation Framework

## What the components mean

- **MACD line:** the spread between a fast and slow exponential moving average.
- **Signal line:** a smoothed version of the MACD line.
- **Histogram:** the distance between MACD and signal. It describes change in their spread; it is not trading volume and does not directly measure return.
- **Zero axis:** MACD above zero means the fast EMA is above the slow EMA; below zero means the opposite.

## Evidence strength

A signal is stronger when several independent observations agree:

1. price structure is trending rather than ranging;
2. the crossover is followed by price continuation;
3. the zero-axis position supports the direction;
4. histogram behavior supports rather than contradicts the move;
5. volume and the higher timeframe confirm the structure.

A signal is weaker when MACD repeatedly crosses near zero, price remains inside a range, volume is light, or the conclusion depends on one ambiguous divergence.

## Common interpretation mistakes

- treating a bullish crossover below zero as equivalent to a confirmed uptrend;
- waiting for a late bearish crossover as the only exit rule;
- calling every shrinking negative histogram bar "bullish";
- comparing MACD values across instruments with different price scales;
- ignoring adjusted/unadjusted price differences and session boundaries;
- optimizing parameters on the same data used to claim success.

## Data caveats

Indicator values can vary between platforms because of:

- EMA seeding and warm-up history;
- adjusted versus unadjusted closes;
- market session and timezone boundaries;
- missing bars or different treatment of zero-volume bars;
- corporate actions and vendor corrections.

Always identify the source and as-of time when precision matters.

## Risk framing

MACD should be one input in a broader process. A complete decision also considers instrument-specific risk, liquidity, volatility, event exposure, position size, transaction costs, tax consequences, and the investor's objectives and risk tolerance.
