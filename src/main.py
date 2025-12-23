"""
Main Entry Point for Saudi Aramco Security Optimization.

Runs experiments comparing Exact (Gurobi) and Heuristic solvers
across technology scenarios: Conservative, Balanced, Future.

Usage:
    uv run python -m src.main                    # Run all scenarios (synthetic data)
    uv run python -m src.main --real-data        # Use real Dhahran locations
    uv run python -m src.main -s Balanced        # Run single scenario
    uv run python -m src.main --heuristic-only   # Skip Gurobi solver
    uv run python -m src.main --verbose          # Show detailed progress
"""
import argparse
import time
import json
from pathlib import Path

from .data_gen import DataGenerator
from .exact_solver import solve_exact
from .heuristic_solver import HeuristicSolver
from .visualization import plot_solution
from .config import RESULTS_DIR
import numpy as np

# Create solutions directory
SOLUTIONS_DIR = RESULTS_DIR / "solutions"
SOLUTIONS_DIR.mkdir(parents=True, exist_ok=True)

# Valid scenarios
VALID_SCENARIOS = ['Conservative', 'Balanced', 'Future']


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Saudi Aramco Security Command Center Location Optimization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run python -m src.main                         Run all scenarios (synthetic)
  uv run python -m src.main --real-data             Use real Dhahran locations
  uv run python -m src.main -s Balanced             Run only Balanced scenario
  uv run python -m src.main -s Conservative Future  Run two scenarios
  uv run python -m src.main --heuristic-only        Skip Gurobi (no license needed)
  uv run python -m src.main --verbose               Show detailed search progress
  uv run python -m src.main --candidates 20 --sites 100  Custom problem size
        """
    )
    
    parser.add_argument(
        '-s', '--scenarios',
        nargs='+',
        choices=VALID_SCENARIOS,
        default=VALID_SCENARIOS,
        metavar='SCENARIO',
        help=f"Scenarios to run. Choices: {', '.join(VALID_SCENARIOS)}. Default: all"
    )
    
    parser.add_argument(
        '--heuristic-only',
        action='store_true',
        help="Run only heuristic solver (no Gurobi license required)"
    )
    
    parser.add_argument(
        '--exact-only',
        action='store_true',
        help="Run only exact Gurobi solver"
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help="Show detailed progress for heuristic solver"
    )
    
    parser.add_argument(
        '--candidates',
        type=int,
        default=15,
        help="Number of candidate facility locations (default: 15)"
    )
    
    parser.add_argument(
        '--sites',
        type=int,
        default=50,
        help="Number of demand sites (default: 50)"
    )
    
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)"
    )
    
    parser.add_argument(
        '--max-iterations',
        type=int,
        default=100,
        help="Maximum local search iterations for heuristic (default: 100)"
    )
    
    parser.add_argument(
        '--no-plots',
        action='store_true',
        help="Skip generating visualization plots"
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help="Custom output filename for results JSON"
    )
    
    parser.add_argument(
        '--real-data',
        action='store_true',
        help="Use real Saudi Aramco Dhahran location data instead of synthetic"
    )
    
    return parser.parse_args()


def extract_gurobi_solution(model, num_I, num_J):
    """
    Helper to extract variable values from Gurobi Model.
    
    Args:
        model: Solved Gurobi model
        num_I: Number of candidate locations
        num_J: Number of demand sites
        
    Returns:
        tuple: (opened_facilities, assignments)
    """
    if not model:
        return [], []
    
    opened = []
    assignments = [-1] * num_J
    
    # Extract y (Opened Facilities)
    for i in range(num_I):
        var = model.getVarByName(f"y[{i}]")
        if var and var.X > 0.5:
            opened.append(i)
            
    # Extract x (Assignments)
    for j in range(num_J):
        for i in range(num_I):
            var = model.getVarByName(f"x[{i},{j}]")
            if var and var.X > 0.5:
                assignments[j] = i
                break
                
    return opened, assignments


def run_experiment(args):
    """
    Run optimization experiment with given configuration.
    
    Args:
        args: Parsed command-line arguments
    """
    # Setup Data Generator
    gen = DataGenerator(
        num_candidates=args.candidates, 
        num_demand_sites=args.sites,
        seed=args.seed,
        use_real_data=args.real_data
    )
    gen.generate_locations()
    
    scenarios = args.scenarios
    run_exact = not args.heuristic_only
    run_heuristic = not args.exact_only
    
    # Results storage
    results = []
    
    print("=" * 75)
    print("Saudi Aramco Security Command Center Optimization")
    print("=" * 75)
    print(f"Configuration: {args.candidates} candidates, {args.sites} demand sites, seed={args.seed}")
    print(f"Scenarios: {', '.join(scenarios)}")
    print(f"Solvers: {'Exact' if run_exact else ''}{' + ' if run_exact and run_heuristic else ''}{'Heuristic' if run_heuristic else ''}")
    print("=" * 75)
    print(f"{'Scenario':<15} | {'Method':<10} | {'Cost':>15} | {'Time (s)':>10} | {'Gap %':>8}")
    print("-" * 75)
    
    for sc in scenarios:
        data = gen.generate_params(scenario=sc)
        scenario_result = {'scenario': sc}
        exact_cost = None
        
        # --- 1. Exact Solution ---
        if run_exact:
            try:
                start_time = time.time()
                exact_cost, model = solve_exact(data)
                exact_time = time.time() - start_time
                
                if model:
                    opened_exact, assign_exact = extract_gurobi_solution(
                        model, data['num_I'], data['num_J']
                    )
                    if not args.no_plots:
                        plot_solution(data, opened_exact, assign_exact, 
                                     title=f"{sc} Scenario - Exact Method")
                    print(f"{sc:<15} | {'Exact':<10} | ${exact_cost:>14,.2f} | {exact_time:>10.3f} | {'N/A':>8}")
                    scenario_result['exact'] = {
                        'cost': exact_cost,
                        'time': exact_time,
                        'facilities': opened_exact,
                        'num_facilities': len(opened_exact)
                    }
                else:
                    print(f"{sc:<15} | {'Exact':<10} | {'INFEASIBLE':>15} | {exact_time:>10.3f} | {'N/A':>8}")
                    scenario_result['exact'] = None
                    exact_cost = None
            except Exception as e:
                print(f"{sc:<15} | {'Exact':<10} | {'ERROR':>15} | {'N/A':>10} | {'N/A':>8}")
                if args.verbose:
                    print(f"  Error: {e}")
                scenario_result['exact'] = {'error': str(e)}
        
        # --- 2. Heuristic Solution ---
        if run_heuristic:
            start_time = time.time()
            heur = HeuristicSolver(
                data, 
                max_iterations=args.max_iterations,
                verbose=args.verbose
            )
            heur.constructive_greedy()
            heur_cost = heur.local_search()
            heur_time = time.time() - start_time
            
            opened_heur = [i for i, val in enumerate(heur.y) if val == 1]
            assign_heur = heur.assignment
            
            if not args.no_plots:
                plot_solution(data, opened_heur, assign_heur, 
                             title=f"{sc} Scenario - Heuristic Method")
            
            # Calculate optimality gap
            if exact_cost and exact_cost > 0:
                gap = (heur_cost - exact_cost) / exact_cost * 100
                gap_str = f"{gap:>7.2f}%"
            else:
                gap = None
                gap_str = "N/A"
            
            print(f"{sc:<15} | {'Heuristic':<10} | ${heur_cost:>14,.2f} | {heur_time:>10.3f} | {gap_str}")
            
            scenario_result['heuristic'] = {
                'cost': heur_cost,
                'time': heur_time,
                'facilities': opened_heur,
                'num_facilities': len(opened_heur),
                'gap_percent': gap
            }
        
        results.append(scenario_result)
        print("-" * 75)
    
    # Export results to JSON
    if args.output:
        results_file = Path(args.output)
    else:
        results_file = SOLUTIONS_DIR / "experiment_results.json"
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nResults exported to: {results_file}")
    print("=" * 75)
    
    return results


def main():
    """Main entry point."""
    args = parse_args()
    run_experiment(args)


if __name__ == "__main__":
    main()