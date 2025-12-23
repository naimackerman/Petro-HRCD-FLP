"""
Data Generator Module for Saudi Aramco Security Optimization.

Supports two modes:
1. Synthetic data: Randomly generated locations around Dhahran
2. Real data: Actual Saudi Aramco facility locations from JSON file
"""
import json
import numpy as np
import pandas as pd
from pathlib import Path
from geopy.distance import geodesic


class DataGenerator:
    def __init__(self, num_candidates=10, num_demand_sites=50, seed=42, use_real_data=False):
        """
        Initialize the data generator.
        
        Args:
            num_candidates: Number of candidate facility locations (synthetic mode)
            num_demand_sites: Number of demand sites (synthetic mode)
            seed: Random seed for reproducibility
            use_real_data: If True, load real Dhahran location data from JSON
        """
        np.random.seed(seed)
        self.use_real_data = use_real_data
        
        # Dhahran center coordinates (approximately 26.30N, 50.13E for Core Area)
        self.center_lat = 26.30
        self.center_lon = 50.13
        
        if not use_real_data:
            self.num_I = num_candidates
            self.num_J = num_demand_sites
        
    def _load_real_data(self):
        """Load real location data from JSON file."""
        data_file = Path(__file__).parent.parent / "data" / "raw" / "dhahran_locations.json"
        
        if not data_file.exists():
            raise FileNotFoundError(
                f"Real data file not found: {data_file}\n"
                "Please ensure data/raw/dhahran_locations.json exists."
            )
        
        with open(data_file, 'r') as f:
            data = json.load(f)
        
        return data
        
    def generate_locations(self):
        """Generate or load candidate and demand site locations."""
        
        if self.use_real_data:
            # Load real Dhahran locations
            data = self._load_real_data()
            
            self.I_coords = [(loc['lat'], loc['lon']) for loc in data['candidate_locations']]
            self.J_coords = [(site['lat'], site['lon']) for site in data['demand_sites']]
            
            # Store additional metadata
            self.I_names = [loc['name'] for loc in data['candidate_locations']]
            self.J_names = [site['name'] for site in data['demand_sites']]
            self.J_tiers = [site['tier'] for site in data['demand_sites']]
            self.J_demands = [site['demand'] for site in data['demand_sites']]
            
            self.num_I = len(self.I_coords)
            self.num_J = len(self.J_coords)
            
            print(f"Loaded real data: {self.num_I} candidates, {self.num_J} demand sites")
        else:
            # Generate synthetic random locations
            def random_coords(n):
                lats = self.center_lat + np.random.uniform(-0.03, 0.03, n)
                lons = self.center_lon + np.random.uniform(-0.03, 0.03, n)
                return list(zip(lats, lons))

            self.I_coords = random_coords(self.num_I)
            self.J_coords = random_coords(self.num_J)
            self.I_names = [f"Candidate-{i}" for i in range(self.num_I)]
            self.J_names = [f"Demand-{j}" for j in range(self.num_J)]
        
        # Calculate Distance Matrix (d_ij) in kilometers
        self.d_ij = np.zeros((self.num_I, self.num_J))
        for i in range(self.num_I):
            for j in range(self.num_J):
                self.d_ij[i][j] = geodesic(self.I_coords[i], self.J_coords[j]).km

    def generate_params(self, scenario='Balanced'):
        """
        Generate cost, demand, and technology parameters based on scenario.
        
        Args:
            scenario: One of 'Conservative', 'Balanced', or 'Future'
            
        Returns:
            dict: Complete parameter dictionary for optimization model
        """
        # 1. Cost Parameters (Monthly basis)
        # Fixed Cost (F_i): Core area locations more expensive
        if self.use_real_data:
            # Higher cost for security hubs and admin buildings
            self.F_i = np.array([22000 if i < 5 else 16000 for i in range(self.num_I)])
        else:
            self.F_i = np.array([20000 if i < self.num_I/2 else 15000 for i in range(self.num_I)])
        
        self.O_i = np.full(self.num_I, 5000)  # Operational cost
        
        # Variable Cost (C_k): Human (expensive) vs Robot (medium)
        self.C_k = {'Robot': 800, 'Human': 3000} 

        # 2. Demand Sites (D_j)
        if self.use_real_data and hasattr(self, 'J_demands'):
            # Use demand values from JSON file
            self.D_j = np.array(self.J_demands)
        else:
            # Generate random demand based on tier distribution
            # Tier 1 (20%): [50, 100] SCU, Tier 2/3 (80%): [10, 30] SCU
            self.D_j = []
            for j in range(self.num_J):
                if np.random.rand() < 0.2:
                    self.D_j.append(np.random.randint(50, 101))
                else:
                    self.D_j.append(np.random.randint(10, 31))
            self.D_j = np.array(self.D_j)

        # 3. Capacity & Utilization
        self.CAP_i = np.full(self.num_I, 100)  # Max slots per facility
        self.U_min = 0.30  # Minimum utilization 30%
        self.S_max = 5.0 if self.use_real_data else 15.0  # Tighter SLA for real data (smaller area)

        # 4. Technology Scenario Settings
        if scenario == 'Conservative':
            self.alpha = 1/3.0
            self.E_k = {'Robot': 1.5, 'Human': 1.0} 
        elif scenario == 'Balanced':
            self.alpha = 1/5.0
            self.E_k = {'Robot': 3.0, 'Human': 1.0}
        elif scenario == 'Future':
            self.alpha = 1/10.0
            self.E_k = {'Robot': 5.0, 'Human': 1.0}
            
        return {
            'num_I': self.num_I, 'num_J': self.num_J,
            'd_ij': self.d_ij, 'D_j': self.D_j,
            'F_i': self.F_i, 'O_i': self.O_i,
            'C_k': self.C_k, 'CAP_i': self.CAP_i,
            'U_min': self.U_min, 'S_max': self.S_max,
            'alpha': self.alpha, 'E_k': self.E_k,
            'coords_I': self.I_coords, 'coords_J': self.J_coords,
            'names_I': self.I_names if hasattr(self, 'I_names') else None,
            'names_J': self.J_names if hasattr(self, 'J_names') else None,
            'use_real_data': self.use_real_data
        }