class GreedyPath:

    def __init__(self, weight: dict[int: int], adjacency: dict[int: list[int]], vertical_squares: int,
               horizontal_squares: int, curr_bikes: int, max_bikes: int, max_time: int):
        self.weight = weight
        self.adjacency = adjacency
        self.v_sq = vertical_squares
        self.h_sq = horizontal_squares
        self.curr_bikes = curr_bikes
        self.max_bikes = max_bikes
        self.max_time = max_time

    def DFS(self, depth: int, path):
        if depth == 0:
            return path
        if depth == 1:
            path.append(self.find_max_route())

    def find_max_route(self, start: int, weight: dict[int: int], curr_bikes: int, max_time: int, drop: bool):
        maximum = 0
        dest = 0
        time = 1
        for cluster in self.weight:
            dist = distance(start=start, end=cluster, h_sq=self.h_sq, v_sq=self.v_sq)
            if dist > max_time and not drop:
                continue
            value = self.weight[cluster]
            if value < curr_bikes - self.max_bikes:
                value = curr_bikes - self.max_bikes
            if value > self.curr_bikes:
                value = self.curr_bikes
            if value < 0 and drop:
                continue
            if abs(value / time_scale(dist)) > abs(maximum / time_scale(time)):
                maximum = value
                dest = cluster
                time = dist
        return dest, time, maximum


def time_scale(time):
    return time ** 0.85


def distance(start: int, end: int, h_sq: int, v_sq: int):
    x_dist = abs((start - end) % h_sq)
    y_dist = abs((start // h_sq) - (end // h_sq))
    return x_dist + y_dist + 1


def get_path(start: int, weight: dict[int: int], adjacency: dict[int: list[int]], vertical_squares: int,
             horizontal_squares: int, curr_bikes: int, max_bikes: int, max_time: int):
    t = 0
    route_dif = {}
    route_log = []
    drop = False
    while t < max_time:

        dest, time, value = find_route(start=start, weight=weight, vertical_squares=vertical_squares,
                                       horizontal_squares=horizontal_squares, curr_bikes=curr_bikes,
                                       max_bikes=max_bikes, adjacency=adjacency, max_time=max_time - t, drop=drop)
        if dest == 0:
            break
        if value < 0:
            action = 'pickup'
        else:
            action = 'drop'
        # print('Curr_bikes:', curr_bikes, 'Time:', t, 'at', start, action, 'at', dest, 'for', (value), 'weight', weight[dest])

        if dest not in route_dif:
            route_dif[dest] = value
        else:
            route_dif[dest] += value

        route_log.append([dest, time, value])
        weight[dest] -= value
        curr_bikes -= value
        start = dest
        t += time
        if t > max_time * 3 / 4 and not drop:
            drop = True
            print("Activated drop only at time:", t)
    print('Curr_bikes:', curr_bikes, 'Time:', t, 'at', dest, action, 'for', value, 'drop', drop)
    # print(weight)
    return route_dif, route_log
