import gurobipy as gp
from gurobipy import GRB
import numpy as np

def create_model(T, K, L, stations, start_levels, optimal_levels, positions, neighbors):
    over_stations, under_stations, balanced_stations = [], [], []
    # Fill over and under stations
    for station in stations:
        if start_levels[station] > optimal_levels[station]:
            over_stations.append(station)
        elif start_levels[station] < optimal_levels[station]:
            under_stations.append(station)
        else:
            balanced_stations.append(station)

    model = gp.Model("bike_rebalancing")

    # Decision variables
    x, y, b = {}, {}, {}
    for t in range(1, T+1):
        for k in range(1, K+1):
            for s in stations:
                x[s, t, k] = model.addVar(name="x_%s,%s,%s" % (s, t, k), vtype=GRB.BINARY)
                y[s, t, k] = model.addVar(name="y_%s,%s,%s" % (s, t, k), vtype=GRB.INTEGER)
            b[t, k] = model.addVar(name="b_%s,%s" % (t, k), vtype=GRB.INTEGER)
    
    # Auxiliary variables for absolute deviation
    deviation = {}
    for s in stations:
        deviation[s] = model.addVar(name="deviation_%s" % s, vtype=GRB.INTEGER)
    
    model.update()
    
    # Objective function: minimize total absolute deviation from optimal levels
    objective = gp.quicksum(deviation[s] for s in stations)
    model.setObjective(objective, sense=GRB.MINIMIZE)
    
    # Constraints:
    
    # Constraint 1: can only move to an adjacent station
    for t in range(2, T+1):
        for k in range(1, K+1):
            for s in stations:
                model.addConstr(x[s,t,k] <= x[s,t-1,k] + gp.quicksum(x[s1,t-1,k] for s1 in neighbors[s]))
    
    
    # Constraint 2: each truck must be at exactly 1 station always
    for t in range(1, T+1):
        for k in range(1, K+1):
            model.addConstr(sum(x[s, t, k] for s in stations) == 1)
    
    # Constraint 3: initialize bike levels at time 1
    for s in stations:
        model.addConstr(sum(y[s, 1, k] for k in range(1, K+1)) == start_levels[s])
    
    # Constraint 4 & 5: rebalancing can only bring a station closer to optimal level
    for t in range(1, T+1):
        for s in over_stations:
            model.addConstr(optimal_levels[s] <= sum(y[s, t, k] for k in range(1, K+1)))
            model.addConstr(sum(y[s, t, k] for k in range(1, K+1)) <= start_levels[s])
        for s in under_stations:
            model.addConstr(start_levels[s] <= sum(y[s, t, k] for k in range(1, K+1)))
            model.addConstr(sum(y[s, t, k] for k in range(1, K+1)) <= optimal_levels[s])
        for s in balanced_stations:
            model.addConstr(sum(y[s, t, k] for k in range(1, K+1)) == start_levels[s])
    
    # Constraint 6: total number of bikes is constant
    for t in range(1, T+1):
        for k in range(1, K+1):
            model.addConstr(sum(y[s, t, k] for s in stations) + b[t, k] == sum(y[s, 1, k] for s in stations) + b[1, k])
    
    # Constraint 7: can move only when truck is at station; number of bikes moved is bounded
    for t in range(2, T+1):
        for k in range(1, K+1):
            for s in stations:
                model.addConstr(y[s, t, k] - y[s, t-1, k] <= L * x[s, t, k])
                model.addConstr(y[s, t-1, k] - y[s, t, k] <= L * x[s, t, k])
    
    # Constraint 8: can either travel or load/unload, not both
    for t in range(2, T+1):
        for k in range(1, K+1):
            for s in over_stations:
                model.addConstr(L * (x[s,t,k] - x[s,t-1,k]) <= L + (y[s,t,k] - y[s,t-1,k]))
                model.addConstr(L * (x[s,t,k] - x[s,t-1,k]) >= -L - (y[s,t,k] - y[s,t-1,k]))
            for s in under_stations:
                model.addConstr(L * (x[s,t,k] - x[s,t-1,k]) <= L - (y[s,t,k] - y[s,t-1,k]))
                model.addConstr(L * (x[s,t,k] - x[s,t-1,k]) >= -L + (y[s,t,k] - y[s,t-1,k]))
    
    # TEST: each truck can only house L bikes
    for k in range(1, K+1):
        for t in range(1,T+1):
            model.addConstr(b[t,k] <= L)
    
    # Absolute deviation constraints
    for s in stations:
        model.addConstr(deviation[s] >= optimal_levels[s] - sum(y[s, T, k] for k in range(1, K+1)))
        model.addConstr(deviation[s] >= sum(y[s, T, k] for k in range(1, K+1)) - optimal_levels[s])
    
    # At beginning and end, there must be no bikes in trucks
    model.addConstr(gp.quicksum(b[T, k] for k in range(1, K+1)) == 0)
    model.addConstr(gp.quicksum(b[1, k] for k in range(1, K+1)) == 0)

    return model