import gurobipy as gp
from gurobipy import GRB
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx

def create_model(T, K, L, stations, start_levels, optimal_levels, positions, neighbors):
    '''
    creates AND optimizes the model for integer programming. solves for the truck routes that get the stations closest to optimal levels
    
    T: int, total time steps
    K: int, total number of trucks
    L: int, max number of bikes a truck can hold
    
    stations: list of the stations/clusters (in my testing i've made this a list of strings, but list of cluster objects should work)
    start_levels: dict, stations --> int, number of bikes at each station/cluster before overnight rebalancing
    optimal_levels: dict, stations --> int, optimal number of bikes after overnight rebalancing
    positions: dict, stations --> tuple, the coordinates of each stations/cluster
    neighbors: dict, stations --> list of stations, maps each station/cluster to a list of stations/clusters that can be moved to in 1 time step
    '''
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

    model.optimize()
    model.update()
    
    return model, x, y, b

def graph_model(x, b, K, T, stations, positions, node_size = 20, title = "Overnight Rebalancing"):
    '''
    graphs the solution that was computed in using the function create_model

    x: the x variable from create_model, which tracks the position of each truck
    b: b variable from create_model, tracks number of bikes in each truck at each time step

    K, T, stations, positions all same as in create_model
    '''
    truck_paths = {}
    
    # if model.status == GRB.OPTIMAL:
    if True:
        for k in range(1, K+1):
            path = []
            for t in range(1, T+1):
                for s in stations:
                    if x[s, t, k].x > 0.5:  # If the truck k is at station s at time t
                        path.append((t, s, '{} bikes'.format(int(b[t,k].x))))
                        break
            truck_paths[k] = path
            # print(f"Truck {k} path: {path}")
    else:
        print("No optimal solution found.")
    
    G = nx.DiGraph()
    
    # Add nodes
    for station in stations:
        G.add_node(station)
    
    # Add edges with arrows for each truck path
    for k, path in truck_paths.items():
        for i in range(len(path) - 1):
            t1, s1 = path[i][:2]
            t2, s2 = path[i + 1][:2]
            G.add_edge(s1, s2, truck=k, time_step=t1)
    
    edge_colors = ['blue', 'red', 'green', 'purple']  # Different colors for different trucks
    
    plt.figure(figsize=(10, 8))
    for k, path in truck_paths.items():
        # edges = [(path[i][1], path[i + 1][1]) for i in range(len(path) - 1)]
        # The above includes time steps where the trucks don't move. Below I have removed such trips
        edges = [(path[i][1], path[i + 1][1]) for i in range(len(path) - 1) if path[i][1] != path[i + 1][1]]
        nx.draw_networkx_edges(G, positions, edgelist=edges, arrowstyle='->', arrowsize=15, 
                               edge_color=edge_colors[k - 1], style='dashed', label=f'Truck {k}')
    
    nx.draw_networkx_nodes(G, positions, node_size= node_size, node_color='lightgray')
    # If we want to add labels we can
    # nx.draw_networkx_labels(G, positions, font_size=10)

    from matplotlib.lines import Line2D
    legend_handles = [Line2D([0], [0], color=edge_colors[k - 1], lw=2, label=f'Truck {k}') for k in range(1, K+1)]
    plt.legend(handles=legend_handles)
    
    plt.title(title)
    plt.show()