#!/usr/bin/env python3
"""Calculate MACD from OHLCV CSV data and emit a compact analysis summary.

The implementation uses SMA-seeded exponential moving averages and has no
third-party dependencies. It is intended for reproducible decision support,
not automated trading.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional, Sequence


@dataclass(frozen=True)
class Bar:
    label: str
    close: float
    volume: Optional[float]


@dataclass(frozen=True)
class Analysis:
    bars: int
    as_of: str
    parameters: dict[str, int]
    close: float
    macd: float
    signal: float
    histogram: float
    zero_axis: str
    line_relation: str
    histogram_momentum: str
    recent_cross: str
    cross_bars_ago: Optional[int]
    price_context: str
    volume_confirmation: str
    evidence: list[str]
    cautions: list[str]


def normalize_header(name: str) -> str:
    return name.strip().lower().replace(" ", "_")


def parse_float(raw: str, field: str, row_number: int) -> float:
    try:
        value = float(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"row {row_number}: invalid {field!r} value {raw!r}") from exc
    if not math.isfinite(value):
        raise ValueError(f"row {row_number}: {field!r} must be finite")
    return value


def read_csv(path: Path) -> list[Bar]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError("CSV has no header row")

        header_map = {normalize_header(name): name for name in reader.fieldnames}
        close_key = header_map.get("close")
        if not close_key:
            raise ValueError("CSV must contain a 'close' column")

        volume_key = header_map.get("volume")
        label_key = next(
            (
                header_map[key]
                for key in ("timestamp", "datetime", "date", "time")
                if key in header_map
            ),
            None,
        )

        bars: list[Bar] = []
        for row_number, row in enumerate(reader, start=2):
            raw_close = (row.get(close_key) or "").strip()
            if not raw_close:
                continue
            close = parse_float(raw_close, "close", row_number)

            volume: Optional[float] = None
            if volume_key:
                raw_volume = (row.get(volume_key) or "").strip()
                if raw_volume:
                    volume = parse_float(raw_volume, "volume", row_number)
                    if volume < 0:
                        raise ValueError(f"row {row_number}: volume cannot be negative")

            label = (row.get(label_key) or "").strip() if label_key else str(len(bars) + 1)
            bars.append(Bar(label=label or str(len(bars) + 1), close=close, volume=volume))

    if not bars:
        raise ValueError("CSV contains no usable rows")
    return bars


def ema(values: Sequence[Optional[float]], period: int) -> list[Optional[float]]:
    if period <= 0:
        raise ValueError("EMA period must be positive")

    output: list[Optional[float]] = [None] * len(values)
    alpha = 2.0 / (period + 1.0)
    seed: list[float] = []
    previous: Optional[float] = None

    for index, value in enumerate(values):
        if value is None:
            continue
        if previous is None:
            seed.append(value)
            if len(seed) < period:
                continue
            previous = statistics.fmean(seed[-period:])
            output[index] = previous
            continue
        previous = alpha * value + (1.0 - alpha) * previous
        output[index] = previous

    return output


def calculate_macd(
    closes: Sequence[float], fast: int, slow: int, signal_period: int
) -> tuple[list[Optional[float]], list[Optional[float]], list[Optional[float]]]:
    if not 0 < fast < slow:
        raise ValueError("periods must satisfy 0 < fast < slow")
    if signal_period <= 0:
        raise ValueError("signal period must be positive")

    values: list[Optional[float]] = list(closes)
    fast_ema = ema(values, fast)
    slow_ema = ema(values, slow)
    macd: list[Optional[float]] = [
        (fast_value - slow_value)
        if fast_value is not None and slow_value is not None
        else None
        for fast_value, slow_value in zip(fast_ema, slow_ema)
    ]
    signal = ema(macd, signal_period)
    histogram: list[Optional[float]] = [
        (macd_value - signal_value)
        if macd_value is not None and signal_value is not None
        else None
        for macd_value, signal_value in zip(macd, signal)
    ]
    return macd, signal, histogram


def last_defined(values: Sequence[Optional[float]]) -> tuple[int, float]:
    for index in range(len(values) - 1, -1, -1):
        if values[index] is not None:
            return index, float(values[index])
    raise ValueError("not enough rows to calculate MACD")


def classify_histogram(histogram: Sequence[Optional[float]], index: int) -> str:
    recent = [value for value in histogram[max(0, index - 3) : index + 1] if value is not None]
    if len(recent) < 3:
        return "insufficient_history"
    deltas = [current - previous for previous, current in zip(recent, recent[1:])]
    tolerance = max(1e-12, max(abs(value) for value in recent) * 1e-6)
    if all(delta > tolerance for delta in deltas):
        return "strengthening"
    if all(delta < -tolerance for delta in deltas):
        return "weakening"
    return "mixed"


def detect_cross(
    macd: Sequence[Optional[float]], signal: Sequence[Optional[float]], index: int, lookback: int
) -> tuple[str, Optional[int]]:
    start = max(1, index - lookback + 1)
    for current in range(index, start - 1, -1):
        values = (macd[current - 1], signal[current - 1], macd[current], signal[current])
        if any(value is None for value in values):
            continue
        previous_diff = float(macd[current - 1]) - float(signal[current - 1])
        current_diff = float(macd[current]) - float(signal[current])
        if previous_diff <= 0 < current_diff:
            return "bullish_cross", index - current
        if previous_diff >= 0 > current_diff:
            return "bearish_cross", index - current
    return "none", None


def classify_price_context(closes: Sequence[float], index: int, window: int = 20) -> str:
    if index < 1:
        return "insufficient_history"
    start = max(0, index - window)
    previous = closes[start:index]
    if len(previous) < 5:
        return "insufficient_history"
    current = closes[index]
    high = max(previous)
    low = min(previous)
    if current > high:
        return "breakout_above_recent_range"
    if current < low:
        return "breakdown_below_recent_range"
    midpoint = (high + low) / 2.0
    if current > midpoint:
        return "upper_half_of_recent_range"
    if current < midpoint:
        return "lower_half_of_recent_range"
    return "middle_of_recent_range"


def classify_volume(bars: Sequence[Bar], index: int, window: int = 20) -> str:
    current = bars[index].volume
    if current is None:
        return "not_available"
    previous = [bar.volume for bar in bars[max(0, index - window) : index] if bar.volume is not None]
    if len(previous) < 5:
        return "insufficient_history"
    average = statistics.fmean(previous)
    if average <= 0:
        return "not_meaningful"
    ratio = current / average
    if ratio >= 1.5:
        return f"high ({ratio:.2f}x_20bar_average)"
    if ratio <= 0.7:
        return f"low ({ratio:.2f}x_20bar_average)"
    return f"normal ({ratio:.2f}x_20bar_average)"


def build_analysis(
    bars: Sequence[Bar], fast: int, slow: int, signal_period: int, cross_lookback: int
) -> Analysis:
    closes = [bar.close for bar in bars]
    macd, signal, histogram = calculate_macd(closes, fast, slow, signal_period)
    index, macd_value = last_defined(macd)
    if signal[index] is None or histogram[index] is None:
        raise ValueError(
            f"not enough rows to calculate MACD({fast},{slow},{signal_period}); "
            f"provide at least {slow + signal_period - 1} usable rows"
        )

    signal_value = float(signal[index])
    histogram_value = float(histogram[index])
    relation_tolerance = max(1e-12, max(abs(macd_value), abs(signal_value)) * 1e-9)
    if abs(macd_value - signal_value) <= relation_tolerance:
        line_relation = "at_signal"
    elif macd_value > signal_value:
        line_relation = "above_signal"
    else:
        line_relation = "below_signal"

    zero_tolerance = max(1e-12, abs(bars[index].close) * 1e-12)
    if abs(macd_value) <= zero_tolerance:
        zero_axis = "at_zero"
    elif macd_value > 0:
        zero_axis = "above_zero"
    else:
        zero_axis = "below_zero"

    histogram_momentum = classify_histogram(histogram, index)
    recent_cross, bars_ago = detect_cross(macd, signal, index, cross_lookback)
    price_context = classify_price_context(closes, index)
    volume_confirmation = classify_volume(bars, index)

    evidence = [
        f"MACD is {zero_axis.replace('_', ' ')} and {line_relation.replace('_', ' ')}.",
        f"Histogram momentum is {histogram_momentum.replace('_', ' ')}.",
        f"Price is in the {price_context.replace('_', ' ')}.",
    ]
    if recent_cross != "none":
        evidence.append(f"A {recent_cross.replace('_', ' ')} occurred {bars_ago} bar(s) ago.")
    if volume_confirmation not in {"not_available", "insufficient_history", "not_meaningful"}:
        evidence.append(f"Current volume is {volume_confirmation.replace('_', ' ')}.")

    cautions = [
        "MACD is derived from past prices and is lagging; it does not predict a reversal by itself.",
        "Crosses in sideways markets can whipsaw; confirm with price structure and, when available, volume.",
        "This output is decision support, not a buy/sell instruction or a guarantee of return.",
    ]

    return Analysis(
        bars=len(bars),
        as_of=bars[index].label,
        parameters={"fast": fast, "slow": slow, "signal": signal_period},
        close=round(closes[index], 8),
        macd=round(macd_value, 8),
        signal=round(signal_value, 8),
        histogram=round(histogram_value, 8),
        zero_axis=zero_axis,
        line_relation=line_relation,
        histogram_momentum=histogram_momentum,
        recent_cross=recent_cross,
        cross_bars_ago=bars_ago,
        price_context=price_context,
        volume_confirmation=volume_confirmation,
        evidence=evidence,
        cautions=cautions,
    )


def render_markdown(analysis: Analysis) -> str:
    cross = analysis.recent_cross.replace("_", " ")
    if analysis.cross_bars_ago is not None:
        cross += f" ({analysis.cross_bars_ago} bar(s) ago)"
    lines = [
        "# MACD Analysis",
        "",
        f"- As of: `{analysis.as_of}`",
        f"- Bars: `{analysis.bars}`",
        f"- Parameters: `{analysis.parameters['fast']}/{analysis.parameters['slow']}/{analysis.parameters['signal']}`",
        f"- Close: `{analysis.close}`",
        f"- MACD / Signal / Histogram: `{analysis.macd}` / `{analysis.signal}` / `{analysis.histogram}`",
        f"- Zero axis: `{analysis.zero_axis}`",
        f"- Line relation: `{analysis.line_relation}`",
        f"- Histogram momentum: `{analysis.histogram_momentum}`",
        f"- Recent cross: `{cross}`",
        f"- Price context: `{analysis.price_context}`",
        f"- Volume: `{analysis.volume_confirmation}`",
        "",
        "## Evidence",
        "",
        *[f"- {item}" for item in analysis.evidence],
        "",
        "## Cautions",
        "",
        *[f"- {item}" for item in analysis.cautions],
    ]
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Calculate MACD from an OHLCV CSV file")
    parser.add_argument("csv_file", type=Path, help="CSV containing at least a close column")
    parser.add_argument("--fast", type=int, default=12, help="fast EMA period (default: 12)")
    parser.add_argument("--slow", type=int, default=26, help="slow EMA period (default: 26)")
    parser.add_argument("--signal", type=int, default=9, help="signal EMA period (default: 9)")
    parser.add_argument("--cross-lookback", type=int, default=5, help="bars to search for a recent cross")
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    parser.add_argument("--pretty", action="store_true", help="pretty-print JSON")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        bars = read_csv(args.csv_file)
        analysis = build_analysis(bars, args.fast, args.slow, args.signal, args.cross_lookback)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.format == "markdown":
        print(render_markdown(analysis))
    else:
        print(json.dumps(asdict(analysis), ensure_ascii=False, indent=2 if args.pretty else None))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
