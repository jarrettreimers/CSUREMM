from cluster_model import ClusterModel
from datetime import timedelta
import numpy as np


class StateOptimization:
    def __init__(self, model: ClusterModel):
        self.model = model

    def optimize(self, length: timedelta, steps=1, time=None, path=None):
        if path:
            if not time:
                print("Time must be specified if path is specified")
            self.model.init_state(path, time=time)
        origin_bike_state = {i: self.model.cluster_dict[i].curr_bikes for i in self.model.cluster_dict}
        origin_time = self.model.curr_time
        origin_in_transit = self.model.in_transit
        end_time = self.model.curr_time + length
        opt_state = origin_bike_state
        for step in range(steps):
            self.model.reset_state(bike_state=opt_state, in_transit=origin_in_transit, time=origin_time)
            while self.model.curr_time < end_time:
                self.model.sim()
            opt_state = {i: opt_state[i] + len(self.model.cluster_dict[i].bad_departures) -
                            len(self.model.cluster_dict[i].bad_arrivals) for i in self.model.cluster_dict}
            for i in opt_state:
                if opt_state[i] < 0:
                    opt_state[i] = 0
                if opt_state[i] > self.model.cluster_dict[i].max_docks:
                    opt_state[i] = self.model.cluster_dict[i].max_docks
        self.model.reset_state(bike_state=origin_bike_state, in_transit=origin_in_transit, time=origin_time)
        return opt_state

    def expected_change(self, num_ticks: int):
        clusters = self.model.cluster_dict.values()

        cluster_to_index = {cluster.name: i for i, cluster in enumerate(clusters)}
        expected_change = np.zeros(len(clusters))
        for tick in range(self.model.curr_tick, num_ticks + self.model.curr_tick):
            rate_vector = np.array([cluster.rate[tick] if cluster.rate[tick] < cluster.curr_bikes
                                    else cluster.curr_bikes for cluster in clusters])
            transition_matrix = np.zeros((len(clusters), len(clusters)))
            for i, cluster in enumerate(clusters):
                for end_cluster in cluster.transition[tick]:
                    j = cluster_to_index[end_cluster]
                    transition_matrix[j, i] = cluster.transition[tick][end_cluster]
            expected_change += np.matmul(transition_matrix, rate_vector) - rate_vector

        return {cluster.name: expected_change[i] for i, cluster in enumerate(clusters)}
