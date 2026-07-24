# MACD Analysis Skill

A portable Skill for conservative MACD interpretation from OHLCV data, market-tool output, or chart screenshots. It combines a reproducible Python calculator with an agent workflow that separates observations from inference and avoids using MACD as a standalone buy/sell signal.

## Features

- Standard `MACD(12,26,9)` with explicit parameter overrides
- Zero-dependency CSV calculator using SMA-seeded EMAs
- Price-structure and volume context
- Recent crossover age and histogram-momentum classification
- Multi-timeframe workflow
- Scenario-based output with confirmation and invalidation conditions
- Safeguards against certainty, cherry-picking, and fabricated data

## Repository Structure

```text
MACD-skill/
├── SKILL.md
├── skill.json
├── agents/
│   └── openai.yaml
├── scripts/
│   └── analyze_macd.py
├── tests/
│   └── test_analyze_macd.py
├── examples/
│   └── sample_ohlcv.csv
└── references/
    └── macd-framework.md
```

## Install in Codex

From a Codex session:

```text
Use $skill-installer to install the skill from https://github.com/luojiyin1987/MACD-skill with path . and name macd.
```

Manual installation:

```bash
SKILLS_DIR="${CODEX_HOME:-$HOME/.codex}/skills"
mkdir -p "$SKILLS_DIR"
git clone https://github.com/luojiyin1987/MACD-skill "$SKILLS_DIR/macd"
chmod +x "$SKILLS_DIR/macd/scripts/analyze_macd.py"
```

Start a new session and invoke it with:

```text
Use $macd to analyze this daily OHLCV CSV. Explain the price structure, MACD state, confirmation, conflicts, and bullish/neutral/bearish scenarios.
```

## Install in Claude Code

```bash
mkdir -p ~/.claude/skills
git clone https://github.com/luojiyin1987/MACD-skill ~/.claude/skills/macd
chmod +x ~/.claude/skills/macd/scripts/analyze_macd.py
```

Then ask:

```text
Use the macd skill to explain this chart. Separate visible facts from interpretation and reduce confidence when the market is ranging.
```

## CSV Usage

The CSV must contain a `close` column. Optional columns include `date`, `timestamp`, and `volume`; other OHLC columns are accepted but not required.

```bash
python3 scripts/analyze_macd.py examples/sample_ohlcv.csv --pretty
```

Markdown output:

```bash
python3 scripts/analyze_macd.py examples/sample_ohlcv.csv --format markdown
```

Custom parameters:

```bash
python3 scripts/analyze_macd.py data.csv --fast 8 --slow 21 --signal 5 --pretty
```

The script fetches no live prices. This keeps the calculation reproducible and avoids hidden API keys, vendor limits, stale cache behavior, and ambiguous market symbols. An Agent can obtain current market data through an available market tool and then apply the workflow in `SKILL.md`.

## Validation

```bash
python3 -m unittest discover -s tests -v
```

## Important Limitations

MACD is calculated from historical prices and is lagging. Crossovers can whipsaw in sideways markets, divergence can persist, and different data vendors can produce slightly different values. The Skill provides decision support and educational analysis, not individualized investment advice or guaranteed returns.

## References

- [TA-Lib Python momentum indicators](https://ta-lib.github.io/ta-lib-python/func_groups/momentum_indicators.html) — common MACD outputs and `12/26/9` defaults
- [FINRA: Risk](https://www.finra.org/investors/investing/investing-basics/risk)
- [FINRA: Know Your Risk Tolerance](https://www.finra.org/investors/insights/know-your-risk-tolerance)

## License

MIT
