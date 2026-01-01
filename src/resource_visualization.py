"""
Resource Allocation Visualization Module.

Creates visualizations comparing resource allocation (human vs robot) across scenarios:
- Detailed breakdown of opened facilities with resource counts (split by method)
- Facility level distribution comparison
"""
import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from .config import FIGURES_DIR

plt.rcParams['pdf.fonttype'] = 42
plt.rcParams['ps.fonttype'] = 42
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'Helvetica', 'DejaVu Sans']

COLORS = {
    'robot': '#3B82F6',      # Vibrant blue
    'human': '#EF4444',      # Vibrant red
    'exact': '#10B981',      # Emerald green
    'heuristic': '#8B5CF6',  # Purple
    'background': '#F8FAFC',  # Light gray
    'grid': '#E2E8F0',        # Light border
    'text': '#1E293B',        # Dark text
    'text_light': '#64748B',  # Muted text
}

SCENARIO_COLORS = {
    'Conservative': '#F59E0B',  # Amber
    'Balanced': '#10B981',       # Emerald
    'Future': '#3B82F6',         # Blue
}

LEVEL_COLORS = {
    'High': '#1A237E',    # Dark blue
    'Medium': '#3F51B5',  # Medium blue
    'Low': '#90CAF9'      # Light blue
}


def load_experiment_results(filepath=None):
    """Load experiment results from JSON file."""
    if filepath is None:
        filepath = Path(__file__).parent.parent / 'results' / 'solutions' / 'experiment_results.json'
    
    with open(filepath, 'r') as f:
        return json.load(f)


def plot_facility_resources_by_method(data=None, method='exact', save_format='pdf'):
    """
    Create detailed breakdown of opened facilities with robot and human counts
    for each scenario, for a single method.
    
    Creates a 1x3 grid: columns = scenarios
    No title/subtitle - clean figure for reports.
    
    Args:
        data: Experiment results data
        method: 'exact' or 'heuristic'
        save_format: 'pdf' or 'png'
    """
    if data is None:
        data = load_experiment_results()
    
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    fig.patch.set_facecolor('white')
    
    for col, scenario_data in enumerate(data):
        scenario = scenario_data['scenario']
        ax = axes[col]
        ax.set_facecolor(COLORS['background'])
        
        method_data = scenario_data[method]
        facilities = method_data['facilities']
        resources = method_data['resources']
        levels = method_data.get('levels', {})
        
        # Prepare data for opened facilities only
        facility_names = []
        robot_counts = []
        human_counts = []
        level_labels = []
        
        for fac_id in facilities:
            fac_key = str(fac_id)
            if fac_key in resources and (resources[fac_key]['robot'] > 0 or resources[fac_key]['human'] > 0):
                facility_names.append(f"CC-{fac_id}")
                robot_counts.append(resources[fac_key]['robot'])
                human_counts.append(resources[fac_key]['human'])
                level_labels.append(levels.get(fac_key, 'N/A'))
        
        if not facility_names:
            ax.text(0.5, 0.5, 'No Active Facilities', ha='center', va='center',
                   fontsize=14, color=COLORS['text_light'], transform=ax.transAxes)
            ax.set_axis_off()
            continue
        
        x = np.arange(len(facility_names))
        width = 0.35
        
        # Create bars
        bars_robot = ax.bar(x - width/2, robot_counts, width, label='Robots', 
                           color=COLORS['robot'], edgecolor='white', linewidth=1.5)
        bars_human = ax.bar(x + width/2, human_counts, width, label='Humans', 
                           color=COLORS['human'], edgecolor='white', linewidth=1.5)
        
        # Add value labels
        for bar in bars_robot:
            height = bar.get_height()
            if height > 0:
                ax.annotate(f'{int(height)}',
                           xy=(bar.get_x() + bar.get_width() / 2, height),
                           xytext=(0, 2), textcoords="offset points",
                           ha='center', va='bottom', fontsize=10, fontweight='bold', 
                           color=COLORS['robot'])
        
        for bar in bars_human:
            height = bar.get_height()
            if height > 0:
                ax.annotate(f'{int(height)}',
                           xy=(bar.get_x() + bar.get_width() / 2, height),
                           xytext=(0, 2), textcoords="offset points",
                           ha='center', va='bottom', fontsize=10, fontweight='bold', 
                           color=COLORS['human'])
        
        # Add level labels below X-axis
        ax.set_xticks(x)
        tick_labels = [f"{name}\n({level})" for name, level in zip(facility_names, level_labels)]
        ax.set_xticklabels(tick_labels, fontsize=10, fontweight='bold')
        
        # Styling
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color(COLORS['grid'])
        ax.spines['bottom'].set_color(COLORS['grid'])
        ax.tick_params(colors=COLORS['text'])
        ax.grid(axis='y', alpha=0.3, color=COLORS['grid'])
        
        max_val = max(max(robot_counts) if robot_counts else 0, 
                     max(human_counts) if human_counts else 0)
        ax.set_ylim(0, max_val * 1.25)
        
        # Scenario label at bottom
        ax.set_xlabel(f'{scenario}', fontsize=14, fontweight='bold', 
                     color=COLORS['text'])
        
        # Y-axis label only for first column
        if col == 0:
            ax.set_ylabel('Resources', fontsize=12, fontweight='bold', color=COLORS['text'])
        
        # Add totals annotation
        total_robots = sum(robot_counts)
        total_humans = sum(human_counts)
        total_text = f"Total: {total_robots} R | {total_humans} H"
        ax.text(0.98, 0.95, total_text, transform=ax.transAxes, fontsize=11,
               ha='right', va='top', fontweight='bold',
               bbox=dict(boxstyle='round,pad=0.3', facecolor='white', 
                        edgecolor=COLORS['grid'], alpha=0.95))
        
        # Show legend only for first plot
        if col == 0:
            ax.legend(fontsize=10, loc='upper left', framealpha=0.95)
    
    plt.tight_layout()
    
    # Save figure
    filename_base = f"facility_resources_{method}"
    if save_format.lower() == "pdf":
        filename = f"{filename_base}.pdf"
        filepath = FIGURES_DIR / filename
        plt.savefig(filepath, format='pdf', bbox_inches='tight', facecolor='white', dpi=150)
    else:
        filename = f"{filename_base}.png"
        filepath = FIGURES_DIR / filename
        plt.savefig(filepath, format='png', bbox_inches='tight', facecolor='white', dpi=300)
    
    print(f"Facility resources ({method}) saved to: {filepath}")
    plt.close()
    return str(filepath)


def plot_command_center_levels(data=None, save_format='pdf'):
    """
    Create a bar chart showing the count of command centers by level (High/Medium/Low)
    for each scenario, comparing exact vs heuristic methods.
    
    Creates a grouped bar chart with scenarios on x-axis, levels as groups.
    """
    if data is None:
        data = load_experiment_results()
    
    scenarios = [d['scenario'] for d in data]
    levels_order = ['High', 'Medium', 'Low']
    
    # Extract level counts for each scenario and method
    exact_counts = {level: [] for level in levels_order}
    heuristic_counts = {level: [] for level in levels_order}
    
    for scenario_data in data:
        exact_levels = scenario_data['exact']['levels']
        heuristic_levels = scenario_data['heuristic']['levels']
        
        # Count levels for exact method
        for level in levels_order:
            count = sum(1 for l in exact_levels.values() if l == level)
            exact_counts[level].append(count)
        
        # Count levels for heuristic method
        for level in levels_order:
            count = sum(1 for l in heuristic_levels.values() if l == level)
            heuristic_counts[level].append(count)
    
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))
    fig.patch.set_facecolor('white')
    
    x = np.arange(len(scenarios))
    width = 0.25
    
    # ========== Left plot: Exact Method ==========
    ax1 = axes[0]
    ax1.set_facecolor(COLORS['background'])
    
    for i, level in enumerate(levels_order):
        bars = ax1.bar(x + (i - 1) * width, exact_counts[level], width, 
                       label=level, color=LEVEL_COLORS[level], edgecolor='white', linewidth=1.5)
        # Add value labels
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax1.annotate(f'{int(height)}',
                           xy=(bar.get_x() + bar.get_width() / 2, height),
                           xytext=(0, 3), textcoords="offset points",
                           ha='center', va='bottom', fontsize=12, fontweight='bold', 
                           color=COLORS['text'])
    
    ax1.set_ylabel('Number of Command Centers', fontsize=14, fontweight='bold', color=COLORS['text'])
    ax1.set_xlabel('Scenario', fontsize=14, fontweight='bold', color=COLORS['text'])
    ax1.set_xticks(x)
    ax1.set_xticklabels(scenarios, fontsize=13, fontweight='bold')
    ax1.legend(title='Level', fontsize=11, title_fontsize=12, loc='upper right', framealpha=0.95)
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    ax1.spines['left'].set_color(COLORS['grid'])
    ax1.spines['bottom'].set_color(COLORS['grid'])
    ax1.tick_params(colors=COLORS['text'])
    ax1.grid(axis='y', alpha=0.3, color=COLORS['grid'])
    
    # Set y-axis limits to show all values clearly
    max_exact = max(max(exact_counts[l]) for l in levels_order)
    ax1.set_ylim(0, max(max_exact * 1.3, 5))
    ax1.set_yticks(range(0, int(max(max_exact * 1.3, 5)) + 1))
    
    # Add method label
    ax1.text(0.5, 1.02, 'Exact Method', transform=ax1.transAxes, fontsize=16, 
            fontweight='bold', color=COLORS['text'], ha='center')
    
    # ========== Right plot: Heuristic Method ==========
    ax2 = axes[1]
    ax2.set_facecolor(COLORS['background'])
    
    for i, level in enumerate(levels_order):
        bars = ax2.bar(x + (i - 1) * width, heuristic_counts[level], width, 
                       label=level, color=LEVEL_COLORS[level], edgecolor='white', linewidth=1.5)
        # Add value labels
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax2.annotate(f'{int(height)}',
                           xy=(bar.get_x() + bar.get_width() / 2, height),
                           xytext=(0, 3), textcoords="offset points",
                           ha='center', va='bottom', fontsize=12, fontweight='bold', 
                           color=COLORS['text'])
    
    ax2.set_ylabel('Number of Command Centers', fontsize=14, fontweight='bold', color=COLORS['text'])
    ax2.set_xlabel('Scenario', fontsize=14, fontweight='bold', color=COLORS['text'])
    ax2.set_xticks(x)
    ax2.set_xticklabels(scenarios, fontsize=13, fontweight='bold')
    ax2.legend(title='Level', fontsize=11, title_fontsize=12, loc='upper right', framealpha=0.95)
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    ax2.spines['left'].set_color(COLORS['grid'])
    ax2.spines['bottom'].set_color(COLORS['grid'])
    ax2.tick_params(colors=COLORS['text'])
    ax2.grid(axis='y', alpha=0.3, color=COLORS['grid'])
    
    # Set y-axis limits to show all values clearly
    max_heur = max(max(heuristic_counts[l]) for l in levels_order)
    ax2.set_ylim(0, max(max_heur * 1.3, 5))
    ax2.set_yticks(range(0, int(max(max_heur * 1.3, 5)) + 1))
    
    # Add method label
    ax2.text(0.5, 1.02, 'Heuristic Method', transform=ax2.transAxes, fontsize=16, 
            fontweight='bold', color=COLORS['text'], ha='center')
    
    plt.tight_layout()
    
    # Save figure
    filename_base = "command_center_levels"
    if save_format.lower() == "pdf":
        filename = f"{filename_base}.pdf"
        filepath = FIGURES_DIR / filename
        plt.savefig(filepath, format='pdf', bbox_inches='tight', facecolor='white', dpi=150)
    else:
        filename = f"{filename_base}.png"
        filepath = FIGURES_DIR / filename
        plt.savefig(filepath, format='png', bbox_inches='tight', facecolor='white', dpi=300)
    
    print(f"Command center levels saved to: {filepath}")
    plt.close()
    return str(filepath)


def generate_all_resource_visualizations(save_format='pdf'):
    """Generate all resource allocation visualizations."""
    print("\n" + "="*60)
    print("Generating Resource Allocation Visualizations")
    print("="*60 + "\n")
    
    data = load_experiment_results()
    
    paths = []
    
    # 1. Facility resources for Exact method
    print("1. Generating facility resources (Exact method)...")
    paths.append(plot_facility_resources_by_method(data, method='exact', save_format=save_format))
    
    # 2. Facility resources for Heuristic method
    print("2. Generating facility resources (Heuristic method)...")
    paths.append(plot_facility_resources_by_method(data, method='heuristic', save_format=save_format))
    
    # 3. Command center levels comparison
    print("3. Generating command center levels comparison...")
    paths.append(plot_command_center_levels(data, save_format))
    
    print("\n" + "="*60)
    print("All visualizations generated successfully!")
    print("="*60 + "\n")
    
    return paths


if __name__ == "__main__":
    generate_all_resource_visualizations(save_format='pdf')
