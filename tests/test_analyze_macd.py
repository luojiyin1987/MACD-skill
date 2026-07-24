from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "analyze_macd.py"
SPEC = importlib.util.spec_from_file_location("analyze_macd", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class MacdTests(unittest.TestCase):
    def test_flat_series_converges_to_zero(self) -> None:
        closes = [100.0] * 80
        macd, signal, histogram = MODULE.calculate_macd(closes, 12, 26, 9)
        index, value = MODULE.last_defined(histogram)
        self.assertGreaterEqual(index, 33)
        self.assertAlmostEqual(value, 0.0, places=10)
        self.assertAlmostEqual(macd[index], 0.0, places=10)
        self.assertAlmostEqual(signal[index], 0.0, places=10)

    def test_rising_series_is_above_zero(self) -> None:
        bars = [MODULE.Bar(str(i), 100.0 + i, 1000.0 + i * 10) for i in range(80)]
        analysis = MODULE.build_analysis(bars, 12, 26, 9, 5)
        self.assertEqual(analysis.zero_axis, "above_zero")
        self.assertGreater(analysis.macd, 0)
        self.assertIn(analysis.line_relation, {"above_signal", "at_signal"})

    def test_falling_series_is_below_zero(self) -> None:
        bars = [MODULE.Bar(str(i), 200.0 - i, 1000.0) for i in range(80)]
        analysis = MODULE.build_analysis(bars, 12, 26, 9, 5)
        self.assertEqual(analysis.zero_axis, "below_zero")
        self.assertLess(analysis.macd, 0)

    def test_rejects_invalid_periods(self) -> None:
        with self.assertRaises(ValueError):
            MODULE.calculate_macd([1.0, 2.0, 3.0], 26, 12, 9)


if __name__ == "__main__":
    unittest.main()
