"""
Exact Solver Module using Gurobi Optimizer.

Implements the Mixed Integer Programming (MIP) model for the 
Saudi Aramco Security Command Center Location Problem as defined in Section 3.
"""
import gurobipy as gp
from gurobipy import GRB


def solve_exact(data):
    """
    Solve the optimization model using Gurobi (Section 4.1 of paper).
    
    Args:
        data: Dictionary containing all problem parameters
        
    Returns:
        tuple: (objective_value, model) if optimal, (None, None) otherwise
    """
    model = gp.Model("Aramco_Security_Location")
    
    # Unpack data
    I = range(data['num_I'])
    J = range(data['num_J'])
    d = data['d_ij']
    
    # --- Decision Variables ---
    # y_i: 1 if command center i is built
    y = model.addVars(I, vtype=GRB.BINARY, name="y")
    # x_ij: 1 if demand site j is served by center i
    x = model.addVars(I, J, vtype=GRB.BINARY, name="x")
    # z_ik: Number of resources (0: Robot, 1: Human)
    z_robot = model.addVars(I, vtype=GRB.INTEGER, name="z_robot")
    z_human = model.addVars(I, vtype=GRB.INTEGER, name="z_human")

    # --- Objective Function (Minimize Total Cost) ---
    fixed_cost = gp.quicksum((data['F_i'][i] + data['O_i'][i]) * y[i] for i in I)
    var_cost = gp.quicksum(data['C_k']['Robot'] * z_robot[i] + 
                           data['C_k']['Human'] * z_human[i] for i in I)
    model.setObjective(fixed_cost + var_cost, GRB.MINIMIZE)

    # --- Constraints ---
    
    # 1. Demand Satisfaction: Each site j must be served by exactly one center i
    model.addConstrs((gp.quicksum(x[i, j] for i in I) == 1 for j in J), name="DemandSat")

    # 2. SLA Compliance: Distance must be <= S_max
    # (Implemented by forcing x=0 for pairs exceeding SLA distance)
    for i in I:
        for j in J:
            if d[i][j] > data['S_max']:
                model.addConstr(x[i, j] == 0, name=f"SLA_{i}_{j}")

    # 3. Logical Link: x_ij <= y_i (can only assign if facility is built)
    model.addConstrs((x[i, j] <= y[i] for i in I for j in J), name="Logical")

    # 4. Service Capacity: Total demand must be covered by resource efficiency
    # Total Demand at i <= (Eff_robot * z_robot + Eff_human * z_human)
    for i in I:
        demand_assigned = gp.quicksum(data['D_j'][j] * x[i, j] for j in J)
        capacity_provided = (data['E_k']['Robot'] * z_robot[i] + 
                             data['E_k']['Human'] * z_human[i])
        model.addConstr(demand_assigned <= capacity_provided, name=f"ServCap_{i}")

    # 5. Physical Capacity: Total resources <= CAP_i
    model.addConstrs((z_robot[i] + z_human[i] <= data['CAP_i'][i] * y[i] for i in I), 
                     name="PhysCap")

    # 6. Supervision Constraint: z_human >= alpha * z_robot
    model.addConstrs((z_human[i] >= data['alpha'] * z_robot[i] for i in I), 
                     name="Supervision")

    # 7. Minimum Utilization: Total resources >= U_min * CAP_i (if y=1)
    model.addConstrs((z_robot[i] + z_human[i] >= 
                      data['U_min'] * data['CAP_i'][i] * y[i] for i in I), 
                     name="MinUtil")

    # Solve the model
    model.optimize()
    
    if model.status == GRB.OPTIMAL:
        return model.objVal, model
    else:
        return None, None