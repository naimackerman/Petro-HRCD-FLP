# Saudi Aramco Security Command Center Optimization

An Operations Research project implementing a **Multi-Level Capacitated Facility Location Problem (ML-CFLP)** to optimize security command center locations and resource allocation for Saudi Aramco's Dhahran district.

## Problem Overview

This project determines:
- **Optimal locations** for multi-level security command centers
- **Facility levels** (Small, Medium, Large) with capacity constraints
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

### Gurobi License Configuration

Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
```

Configure your Gurobi license:

**For WLS License (Cloud):**
```env
GUROBI_LICENSE_TYPE=wls
GUROBI_LICENSE_ID=your_license_id
GUROBI_WLSACCESSID=your_access_id
GUROBI_WLSSECRET=your_secret
```

**For File License (Local):**
```env
GUROBI_LICENSE_TYPE=file
# Optional: GUROBI_LICENSE_FILE=/path/to/gurobi.lic
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

# Save solutions for later visualization
uv run python -m src.main --save-solutions
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
| `--max-iterations N` | Maximum local search iterations (default: 100) |
| `--no-plots` | Skip visualizations |
| `--save-solutions` | Save solutions for later visualization |
| `--output FILE` | Custom output filename for results JSON |

### Solution Management

Saved solutions can be managed and visualized without re-running solvers:

```bash
# List all saved solutions
uv run python -m src.solution_io --list

# Visualize a saved solution
uv run python -m src.solution_io --load <filename>

# Compare exact vs heuristic for a scenario
uv run python -m src.solution_io --compare Balanced

# Delete a saved solution
uv run python -m src.solution_io --delete <filename>
```

## Output Files

- `results/figures/*.pdf` - Network visualization plots (LaTeX-ready)
- `results/figures/*.png` - Network visualization plots (web/preview)
- `results/solutions/experiment_results.json` - Detailed results (JSON)
- `results/solutions/experiment_results.xlsx` - Detailed results (Excel)
- `results/saved_solutions/` - Saved solutions for later visualization

### Converting Figures to PDF

For LaTeX documents, convert existing PNG figures to optimized PDFs:

```bash
uv run python -m src.convert_figures_to_pdf
```

## Project Structure

```
aramco_security_opt/
├── src/
│   ├── config.py               # Path configuration
│   ├── convert_figures_to_pdf.py  # PNG → PDF converter for LaTeX
│   ├── data_gen.py             # Data generator (synthetic + real)
│   ├── exact_solver.py         # Gurobi MIP model
│   ├── heuristic_solver.py     # Greedy + Local Search
│   ├── main.py                 # CLI entry point
│   ├── solution_io.py          # Save/load solutions
│   └── visualization.py        # Plot generation
├── data/                       # Real location data (JSON)
├── results/
│   ├── figures/                # Visualization outputs
│   ├── solutions/              # Experiment results
│   └── saved_solutions/        # Saved solutions for re-visualization
├── report/
│   ├── main.tex                # Research paper
│   └── figures/                # LaTeX figures
├── .env.example                # Environment template
└── pyproject.toml              # Dependencies
```

## Dependencies

Core dependencies managed via `pyproject.toml`:

- **gurobipy** - Gurobi optimizer for exact MIP solving
- **numpy/pandas** - Data manipulation
- **matplotlib** - Visualization
- **contextily** - Geographic basemaps
- **geopy** - Distance calculations
- **adjusttext** - Label adjustment in plots
- **openpyxl** - Excel export
- **python-dotenv** - Environment configuration

## Heuristic Algorithm

The heuristic implements a two-stage approach:

1. **Constructive Greedy**: Assigns demand sites to facilities in order of demand priority (SCU demand × distance)
2. **Local Search**: Improves solution using:
   - **Shift Move**: Relocate single demand site to a different facility
   - **Swap Move**: Exchange two sites between facilities
   - **Drop Move**: Close low-utilization facility and redistribute sites
   - **Open Move**: Open a new facility to reduce travel distances

## Mathematical Formulation

**Objective**: Minimize total cost (facility fixed cost + resource cost + travel cost)

**Constraints**:
- Each demand site assigned to exactly one facility
- Facility capacity (min/max) based on level
- SLA response time requirements
- Human supervision of robots

## License

Academic research project.
