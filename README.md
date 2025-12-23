# Saudi Aramco Security Command Center Optimization

An Operations Research project implementing a Capacitated Facility Location Problem (CFLP) to optimize security command center locations and resource allocation for Saudi Aramco's Dhahran district.

## Problem Overview

This project determines:
- **Optimal locations** for security command centers
- **Resource mix** (humans vs robots) at each center
- **Demand assignments** connecting sites to centers

While minimizing total cost and respecting SLA, capacity, and supervision constraints.

## Technology Scenarios

| Scenario | Supervision Ratio | Robot Efficiency | Context |
|----------|-------------------|------------------|---------|
| Conservative | 1:3 | 1.5x | Early adoption |
| Balanced | 1:5 | 3.0x | Current technology |
| Future | 1:10 | 5.0x | High AI maturity |

## Prerequisites

1. **Python 3.11+**
2. **uv**: https://docs.astral.sh/uv/
3. **Gurobi** (optional): https://www.gurobi.com/academia/

## Installation

```bash
cd aramco_security_opt
uv sync
```

## Usage

```bash
# Run all scenarios (synthetic data)
uv run python -m src.main

# Use real Saudi Aramco Dhahran locations
uv run python -m src.main --real-data

# Single scenario
uv run python -m src.main -s Balanced

# Heuristic only (no Gurobi needed)
uv run python -m src.main --heuristic-only

# Verbose mode (see local search progress)
uv run python -m src.main -s Balanced --verbose

# Custom problem size (synthetic mode only)
uv run python -m src.main --candidates 20 --sites 100
```

### CLI Options

| Option | Description |
|--------|-------------|
| `-s, --scenarios` | Scenarios to run (Conservative, Balanced, Future) |
| `--real-data` | Use real Saudi Aramco Dhahran facility locations |
| `--heuristic-only` | Skip Gurobi solver |
| `--exact-only` | Skip heuristic solver |
| `-v, --verbose` | Show detailed search progress |
| `--candidates N` | Number of facility candidates (default: 15) |
| `--sites N` | Number of demand sites (default: 50) |
| `--seed N` | Random seed (default: 42) |
| `--no-plots` | Skip visualizations |

## Results (Default Configuration)

| Scenario | Exact Cost | Heuristic | Gap | Facilities |
|----------|------------|-----------|-----|------------|
| Conservative | $1,399,600 | $1,433,800 | 2.44% | 9 → 10 |
| Balanced | $879,600 | $889,600 | 1.14% | 7 |
| Future | $512,400 | $517,400 | 0.98% | 5 |

## Output Files

- `results/figures/*.png` - Network visualization plots
- `results/solutions/experiment_results.json` - Detailed results

## Project Structure

```
aramco_security_opt/
├── src/
│   ├── config.py           # Path configuration
│   ├── data_gen.py         # Data generator
│   ├── exact_solver.py     # Gurobi MIP model
│   ├── heuristic_solver.py # Greedy + Local Search
│   ├── main.py             # CLI entry point
│   └── visualization.py    # Plot generation
├── results/                # Output directory
├── report/main.tex         # Research paper
└── pyproject.toml          # Dependencies
```

## Heuristic Algorithm

The heuristic implements a two-stage approach:

1. **Constructive Greedy**: Assigns demand sites to facilities in order of demand priority
2. **Local Search**: Improves solution using:
   - **Shift Move**: Relocate single demand site
   - **Swap Move**: Exchange two sites between facilities
   - **Drop Move**: Close low-utilization facility
   - **Open Move**: Open new facility for better coverage

## License

Academic research project.
