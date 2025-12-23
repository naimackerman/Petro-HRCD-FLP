"""
Visualization Module for Solution Plotting.

Creates geographic network plots showing:
- Command center locations (active vs unused)
- Demand site locations (sized by demand)
- Assignment connections between centers and demand sites
- OpenStreetMap basemap for geographic context
"""
import matplotlib.pyplot as plt
import numpy as np
import contextily as ctx
from .config import FIGURES_DIR

# Configure matplotlib for PDF output optimization
plt.rcParams['pdf.fonttype'] = 42  # TrueType fonts for better compatibility
plt.rcParams['ps.fonttype'] = 42   # TrueType fonts in PostScript


def plot_solution(data, opened_facilities, assignments, title="Optimization Result", 
                  save_format="pdf"):
    """
    Visualize the location map and assignments on a geographic basemap.
    
    Args:
        data: Dictionary containing coordinate and demand data
        opened_facilities: List of opened facility indices (y_i = 1)
        assignments: Mapping of demand site j to facility i (list format: assignments[j] = i)
        title: Plot title string
        save_format: Output format - 'pdf' (recommended for LaTeX) or 'png'
        
    Returns:
        str: Path to saved figure
    """
    coords_I = np.array(data['coords_I'])  # (lat, lon)
    coords_J = np.array(data['coords_J'])  # (lat, lon)
    
    # Create figure with larger size for map detail
    fig, ax = plt.subplots(figsize=(14, 12))
    
    # Calculate bounds for the map with padding
    all_lats = np.concatenate([coords_I[:, 0], coords_J[:, 0]])
    all_lons = np.concatenate([coords_I[:, 1], coords_J[:, 1]])
    
    lat_margin = (all_lats.max() - all_lats.min()) * 0.15
    lon_margin = (all_lons.max() - all_lons.min()) * 0.15
    
    # Set axis limits (longitude = x, latitude = y)
    ax.set_xlim(all_lons.min() - lon_margin, all_lons.max() + lon_margin)
    ax.set_ylim(all_lats.min() - lat_margin, all_lats.max() + lat_margin)
    
    # 1. Draw Assignment Lines (draw first so they appear behind points)
    for j, i in enumerate(assignments):
        if i != -1:  # If assigned
            start_point = coords_I[i]
            end_point = coords_J[j]
            ax.plot([start_point[1], end_point[1]], 
                    [start_point[0], end_point[0]], 
                    c='#FF6B6B', linestyle='-', alpha=0.5, linewidth=1.2, zorder=2)
    
    # 2. Plot All Candidate Locations (Gray = Not Built)
    ax.scatter(coords_I[:, 1], coords_I[:, 0], 
               c='#808080', marker='s', s=120, 
               label='Unused Candidate', edgecolors='white', linewidths=1.5, zorder=4)

    # 3. Plot Opened Command Centers (Red = Built)
    if len(opened_facilities) > 0:
        opened_coords = coords_I[opened_facilities]
        ax.scatter(opened_coords[:, 1], opened_coords[:, 0], 
                   c='#E63946', marker='s', s=200, 
                   label='Active Command Center', edgecolors='white', linewidths=2, zorder=6)
        
        # Label facility IDs with background for visibility
        for idx in opened_facilities:
            ax.annotate(f"CC-{idx}", 
                       xy=(coords_I[idx, 1], coords_I[idx, 0]),
                       xytext=(0, 8), textcoords='offset points',
                       fontsize=9, ha='center', fontweight='bold',
                       color='white',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='#E63946', 
                                edgecolor='white', alpha=0.9),
                       zorder=7)

    # 4. Plot Demand Sites (Blue, sized by demand level)
    sizes = data['D_j'] * 2.5  # Scale factor for visibility
    ax.scatter(coords_J[:, 1], coords_J[:, 0], 
               c='#457B9D', marker='o', s=sizes, 
               label='Demand Site', alpha=0.8, edgecolors='white', linewidths=1, zorder=5)

    # 5. Add OpenStreetMap basemap
    try:
        ctx.add_basemap(ax, crs="EPSG:4326", 
                       source=ctx.providers.OpenStreetMap.Mapnik,
                       zoom=14, alpha=0.8)
    except Exception as e:
        # Fallback: try CartoDB Positron (lighter style)
        try:
            ctx.add_basemap(ax, crs="EPSG:4326", 
                           source=ctx.providers.CartoDB.Positron,
                           zoom=14, alpha=0.8)
        except:
            # If all basemaps fail, add a simple background color
            ax.set_facecolor('#F5F5DC')
            print(f"  Note: Could not load basemap tiles (offline?). Using plain background.")

    # Formatting
    ax.set_title(f"Aramco Security Network: {title}", fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel("Longitude", fontsize=12)
    ax.set_ylabel("Latitude", fontsize=12)
    
    # Legend with better styling
    legend = ax.legend(loc='upper right', fontsize=10, framealpha=0.95)
    legend.get_frame().set_facecolor('white')
    legend.get_frame().set_edgecolor('#CCCCCC')
    
    # Add summary stats as text box
    num_open = len(opened_facilities)
    total_demand = sum(data['D_j'])
    stats_text = f"Open Facilities: {num_open}/{len(coords_I)}\nTotal Demand: {total_demand:,} SCU"
    ax.text(0.02, 0.02, stats_text, transform=ax.transAxes, fontsize=10,
           verticalalignment='bottom', horizontalalignment='left',
           bbox=dict(boxstyle='round,pad=0.5', facecolor='white', 
                    edgecolor='#CCCCCC', alpha=0.9))
    
    plt.tight_layout()
    
    # Determine file extension and save settings based on format
    filename_base = f"result_{title.replace(' ', '_').lower()}"
    
    if save_format.lower() == "pdf":
        # PDF format - ideal for LaTeX, smaller size, vector graphics
        filename = f"{filename_base}.pdf"
        filepath = FIGURES_DIR / filename
        plt.savefig(filepath, format='pdf', bbox_inches='tight', 
                   facecolor='white', dpi=150)  # Lower DPI for PDF (vector-based)
        print(f"PDF visualization saved to: {filepath}")
    else:
        # PNG format - raster image for web/presentations
        filename = f"{filename_base}.png"
        filepath = FIGURES_DIR / filename
        plt.savefig(filepath, format='png', bbox_inches='tight', 
                   facecolor='white', dpi=300)
        print(f"PNG visualization saved to: {filepath}")
    
    plt.close()  # Close plot to free memory
    
    return str(filepath)


def regenerate_all_figures_as_pdf():
    """
    Utility function to regenerate existing PNG figures as PDFs.
    This is useful for converting existing results to LaTeX-friendly format.
    """
    import os
    from pathlib import Path
    
    png_files = list(FIGURES_DIR.glob("*.png"))
    
    if not png_files:
        print("No PNG files found in figures directory.")
        return []
    
    pdf_paths = []
    for png_path in png_files:
        pdf_filename = png_path.stem + ".pdf"
        pdf_path = FIGURES_DIR / pdf_filename
        
        # Use matplotlib to convert PNG to PDF with optimization
        try:
            from PIL import Image
            img = Image.open(png_path)
            # Convert to RGB if necessary (PDF doesn't support RGBA well)
            if img.mode == 'RGBA':
                # Create white background
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])  # 3 is the alpha channel
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Save as PDF with reduced quality for smaller size
            img.save(pdf_path, 'PDF', resolution=150, optimize=True)
            
            # Check file sizes
            png_size = png_path.stat().st_size / (1024 * 1024)  # MB
            pdf_size = pdf_path.stat().st_size / (1024 * 1024)  # MB
            
            print(f"Converted: {png_path.name} ({png_size:.2f}MB) -> {pdf_filename} ({pdf_size:.2f}MB)")
            pdf_paths.append(str(pdf_path))
            
        except Exception as e:
            print(f"Error converting {png_path.name}: {e}")
    
    return pdf_paths