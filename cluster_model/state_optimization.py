from cluster_model import ClusterModel
from datetime import timedelta


class StateOptimization:
    def __init__(self, model: ClusterModel):
        self.model = model

    def optimize(self, length: timedelta, time=None, path=None):
        if path:
            if not time:
                print("Time must be specified if path is specified")
            self.model.init_state(path, time=time)
        end_time = self.model.curr_time + length
        while self.model.curr_time < end_time:
            self.model.sim()

