"""
Heuristic Solver Module for Large-Scale Instances.

Implements a two-stage approach:
1. Constructive Greedy Heuristic for initial feasible solution
2. Local Search Improvement (Shift, Swap, Drop/Open moves)

As described in Section 4.2 of the research paper.
"""
import numpy as np
import math


class HeuristicSolver:
    def __init__(self, data, max_iterations=100, verbose=False):
        """
        Initialize the heuristic solver.
        
        Args:
            data: Dictionary containing all problem parameters
            max_iterations: Maximum local search iterations (default: 100)
            verbose: If True, print progress messages
        """
        self.data = data
        self.num_I = data['num_I']
        self.num_J = data['num_J']
        self.max_iterations = max_iterations
        self.verbose = verbose
        # Solution state
        self.y = np.zeros(self.num_I, dtype=int)  # Facility open/closed
        self.assignment = [-1] * self.num_J  # x_ij: which facility serves each demand
        self.resources = {i: {'human': 0, 'robot': 0} for i in range(self.num_I)}

    def calculate_resource_mix(self, total_demand, facility_idx):
        """
        Calculate optimal Robot & Human count for a given demand level.
        
        Uses simple linear system to satisfy demand & supervision at minimal cost:
        - Minimize: C_r * R + C_h * H
        - Subject to: E_r * R + E_h * H >= Demand
        -             H >= alpha * R (supervision constraint)
        
        Heuristic approach: Assume H = alpha * R (lower bound of supervision)
        Then: Total Eff = E_r * R + E_h * (alpha * R) = R(E_r + alpha * E_h)
        So: R = Demand / (E_r + alpha * E_h)
        
        Args:
            total_demand: Total demand to be satisfied
            facility_idx: Index of the facility
            
        Returns:
            tuple: (required_robots, required_humans) or None if infeasible
        """
        if total_demand <= 0:
            return 0, 0
            
        denom = self.data['E_k']['Robot'] + self.data['alpha'] * self.data['E_k']['Human']
        req_robots = math.ceil(total_demand / denom)
        req_humans = math.ceil(self.data['alpha'] * req_robots)
        
        # Ensure minimum utilization is met if facility is open
        min_resources = math.ceil(self.data['U_min'] * self.data['CAP_i'][facility_idx])
        if req_robots + req_humans < min_resources:
            # Increase robots to meet minimum utilization
            extra_needed = min_resources - (req_robots + req_humans)
            req_robots += extra_needed
            req_humans = math.ceil(self.data['alpha'] * req_robots)
        
        # Check Physical Capacity constraint
        if req_robots + req_humans > self.data['CAP_i'][facility_idx]:
            return None  # Capacity exceeded
            
        return req_robots, req_humans

    def _get_facility_demand(self, facility_idx):
        """Calculate total demand currently assigned to a facility."""
        total = 0
        for j in range(self.num_J):
            if self.assignment[j] == facility_idx:
                total += self.data['D_j'][j]
        return total

    def _get_facility_sites(self, facility_idx):
        """Get list of demand site indices assigned to a facility."""
        return [j for j in range(self.num_J) if self.assignment[j] == facility_idx]

    def _update_facility_state(self):
        """Update y and resources state based on current assignments."""
        for i in range(self.num_I):
            demand = self._get_facility_demand(i)
            if demand > 0:
                self.y[i] = 1
                res = self.calculate_resource_mix(demand, i)
                if res:
                    self.resources[i] = {'robot': res[0], 'human': res[1]}
            else:
                self.y[i] = 0
                self.resources[i] = {'robot': 0, 'human': 0}

    def _can_serve(self, facility_idx, demand_site_idx):
        """Check if facility can serve demand site (SLA compliance)."""
        return self.data['d_ij'][facility_idx][demand_site_idx] <= self.data['S_max']

    def constructive_greedy(self):
        """
        Stage 1: Constructive Greedy Heuristic
        
        Generate initial feasible solution using distance-based greedy strategy:
        1. Sort demand sites by priority (highest demand first)
        2. For each site, find valid candidates satisfying SLA
        3. Assign to candidate minimizing marginal cost
        4. Update resource allocation
        """
        if self.verbose:
            print("Stage 1: Constructive Greedy Heuristic")
            
        # 1. Sort demand sites (Highest to Lowest demand)
        sorted_J = np.argsort(self.data['D_j'])[::-1]
        
        for j in sorted_J:
            best_i = -1
            min_marginal_cost = float('inf')
            
            # Find candidates satisfying SLA constraint
            valid_candidates = [i for i in range(self.num_I) if self._can_serve(i, j)]
            
            for i in valid_candidates:
                # Calculate current demand already assigned to facility i
                current_demand = self._get_facility_demand(i)
                new_demand = current_demand + self.data['D_j'][j]
                
                # Check resource feasibility
                res = self.calculate_resource_mix(new_demand, i)
                if res is None:
                    continue
                r_new, h_new = res
                
                # Calculate marginal cost
                cost_new = (r_new * self.data['C_k']['Robot'] + 
                            h_new * self.data['C_k']['Human'])
                
                # Add fixed cost if facility not yet opened
                if self.y[i] == 0:
                    cost_new += self.data['F_i'][i] + self.data['O_i'][i]
                
                # Select minimum cost option
                if cost_new < min_marginal_cost:
                    min_marginal_cost = cost_new
                    best_i = i
            
            if best_i != -1:
                self.assignment[j] = best_i
                self.y[best_i] = 1  # Mark facility as open
                # Update resource state
                demand = self._get_facility_demand(best_i)
                res = self.calculate_resource_mix(demand, best_i)
                if res:
                    self.resources[best_i] = {'robot': res[0], 'human': res[1]}
        
        if self.verbose:
            print(f"  Initial solution cost: ${self.calculate_total_cost():,.2f}")
            print(f"  Opened facilities: {sum(self.y)}")
    
    def calculate_total_cost(self):
        """
        Calculate global total cost for current solution.
        
        Returns:
            float: Total cost (fixed + variable), or inf if infeasible
        """
        total_cost = 0
        facility_demands = {i: 0 for i in range(self.num_I)}
        
        for j, i_assigned in enumerate(self.assignment):
            if i_assigned == -1:
                return float('inf')  # Penalty for unassigned demand
            facility_demands[i_assigned] += self.data['D_j'][j]
            
        for i in range(self.num_I):
            if facility_demands[i] > 0:
                res = self.calculate_resource_mix(facility_demands[i], i)
                if res is None:
                    return float('inf')  # Constraint violation
                r, h = res
                
                # Fixed costs
                total_cost += self.data['F_i'][i] + self.data['O_i'][i]
                # Variable costs
                total_cost += (r * self.data['C_k']['Robot'] + 
                               h * self.data['C_k']['Human'])
                    
        return total_cost

    def _shift_move(self):
        """
        Shift Move: Try moving demand site j from current center to a different one.
        
        Returns:
            bool: True if an improving move was found
        """
        current_cost = self.calculate_total_cost()
        
        for j in range(self.num_J):
            original_i = self.assignment[j]
            
            for k in range(self.num_I):
                if k == original_i:
                    continue
                if not self._can_serve(k, j):
                    continue
                
                self.assignment[j] = k
                new_cost = self.calculate_total_cost()
                
                if new_cost < current_cost:
                    self._update_facility_state()
                    if self.verbose:
                        print(f"  Shift: site {j} from facility {original_i} to {k}, "
                              f"saving ${current_cost - new_cost:,.2f}")
                    return True
                else:
                    self.assignment[j] = original_i
                    
        return False

    def _swap_move(self):
        """
        Swap Move: Exchange assignments of two demand sites between two facilities.
        
        This can help escape local optima by simultaneously adjusting two assignments.
        
        Returns:
            bool: True if an improving move was found
        """
        current_cost = self.calculate_total_cost()
        
        for j1 in range(self.num_J):
            i1 = self.assignment[j1]
            
            for j2 in range(j1 + 1, self.num_J):
                i2 = self.assignment[j2]
                
                # Only swap if they are assigned to different facilities
                if i1 == i2:
                    continue
                
                # Check SLA compliance for the swap
                if not self._can_serve(i2, j1) or not self._can_serve(i1, j2):
                    continue
                
                # Perform swap
                self.assignment[j1] = i2
                self.assignment[j2] = i1
                
                new_cost = self.calculate_total_cost()
                
                if new_cost < current_cost:
                    self._update_facility_state()
                    if self.verbose:
                        print(f"  Swap: sites ({j1}, {j2}) between facilities ({i1}, {i2}), "
                              f"saving ${current_cost - new_cost:,.2f}")
                    return True
                else:
                    # Revert swap
                    self.assignment[j1] = i1
                    self.assignment[j2] = i2
                    
        return False

    def _drop_move(self):
        """
        Drop Move: Try closing a facility by redistributing its demand to neighbors.
        
        This move attempts to close low-utilization facilities and consolidate
        demand into fewer, more efficient command centers.
        
        Returns:
            bool: True if an improving move was found
        """
        current_cost = self.calculate_total_cost()
        
        # Get list of currently open facilities
        open_facilities = [i for i in range(self.num_I) if self.y[i] == 1]
        
        # Sort by demand (try dropping low-demand facilities first)
        open_facilities.sort(key=lambda i: self._get_facility_demand(i))
        
        for drop_i in open_facilities:
            sites_at_i = self._get_facility_sites(drop_i)
            if not sites_at_i:
                continue
            
            # Try to redistribute all sites from drop_i to other open facilities
            original_assignments = {j: self.assignment[j] for j in sites_at_i}
            redistribution_possible = True
            
            for j in sites_at_i:
                # Find alternative facility for this site
                best_alt = -1
                min_increase = float('inf')
                
                for alt_i in open_facilities:
                    if alt_i == drop_i:
                        continue
                    if not self._can_serve(alt_i, j):
                        continue
                    
                    # Check if alt_i can handle the extra demand
                    current_alt_demand = self._get_facility_demand(alt_i)
                    new_alt_demand = current_alt_demand + self.data['D_j'][j]
                    
                    res = self.calculate_resource_mix(new_alt_demand, alt_i)
                    if res is None:
                        continue
                    
                    # Calculate cost increase at alternative
                    r_new, h_new = res
                    res_old = self.calculate_resource_mix(current_alt_demand, alt_i)
                    r_old, h_old = res_old if res_old else (0, 0)
                    
                    increase = ((r_new - r_old) * self.data['C_k']['Robot'] + 
                               (h_new - h_old) * self.data['C_k']['Human'])
                    
                    if increase < min_increase:
                        min_increase = increase
                        best_alt = alt_i
                
                if best_alt == -1:
                    redistribution_possible = False
                    break
                else:
                    self.assignment[j] = best_alt
            
            if redistribution_possible:
                new_cost = self.calculate_total_cost()
                
                if new_cost < current_cost:
                    self._update_facility_state()
                    if self.verbose:
                        print(f"  Drop: closed facility {drop_i}, redistributed {len(sites_at_i)} sites, "
                              f"saving ${current_cost - new_cost:,.2f}")
                    return True
            
            # Revert assignments if not beneficial
            for j, orig_i in original_assignments.items():
                self.assignment[j] = orig_i
                    
        return False

    def _open_move(self):
        """
        Open Move: Try opening a new facility to reduce travel distances.
        
        This move identifies clusters of demand sites that could be better served
        by opening a currently closed facility nearby.
        
        Returns:
            bool: True if an improving move was found
        """
        current_cost = self.calculate_total_cost()
        
        # Get closed facilities
        closed_facilities = [i for i in range(self.num_I) if self.y[i] == 0]
        
        for new_i in closed_facilities:
            # Find demand sites that could be served by this facility
            potential_sites = [j for j in range(self.num_J) if self._can_serve(new_i, j)]
            
            if not potential_sites:
                continue
            
            # Calculate potential savings for each site
            site_savings = []
            for j in potential_sites:
                current_i = self.assignment[j]
                current_dist = self.data['d_ij'][current_i][j]
                new_dist = self.data['d_ij'][new_i][j]
                
                # Consider moving if new facility is closer
                if new_dist < current_dist:
                    site_savings.append((j, current_dist - new_dist))
            
            # Sort by savings (best first)
            site_savings.sort(key=lambda x: x[1], reverse=True)
            
            # Try moving top sites to new facility
            if len(site_savings) >= 2:  # Need at least 2 sites to justify opening
                original_assignments = {}
                
                # Move top sites (up to 10) to new facility
                for j, _ in site_savings[:10]:
                    original_assignments[j] = self.assignment[j]
                    self.assignment[j] = new_i
                
                new_cost = self.calculate_total_cost()
                
                if new_cost < current_cost:
                    self._update_facility_state()
                    if self.verbose:
                        print(f"  Open: opened facility {new_i} with {len(original_assignments)} sites, "
                              f"saving ${current_cost - new_cost:,.2f}")
                    return True
                else:
                    # Revert
                    for j, orig_i in original_assignments.items():
                        self.assignment[j] = orig_i
                    
        return False

    def local_search(self):
        """
        Stage 2: Local Search Improvement
        
        Implements multiple neighborhood structures:
        - Shift Move: Move single demand site to different facility
        - Swap Move: Exchange two demand sites between facilities
        - Drop Move: Close facility and redistribute demand
        - Open Move: Open new facility to reduce distances
        
        Uses first-improvement strategy with cycling through move types.
        
        Returns:
            float: Final cost after improvement
        """
        if self.verbose:
            print("Stage 2: Local Search Improvement")
        
        iteration = 0
        improving = True
        
        while improving and iteration < self.max_iterations:
            improving = False
            iteration += 1
            
            # Try each move type in sequence
            # Shift moves (most common improvement)
            if self._shift_move():
                improving = True
                continue
            
            # Swap moves (escape local optima)
            if self._swap_move():
                improving = True
                continue
            
            # Drop moves (consolidation)
            if self._drop_move():
                improving = True
                continue
            
            # Open moves (expansion for better coverage)
            if self._open_move():
                improving = True
                continue
        
        final_cost = self.calculate_total_cost()
        
        if self.verbose:
            print(f"Local search completed after {iteration} iterations")
            print(f"  Final cost: ${final_cost:,.2f}")
            print(f"  Final facilities: {sum(self.y)}")
        
        return final_cost