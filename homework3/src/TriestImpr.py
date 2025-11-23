import random
from collections import defaultdict
from src.ReservoirSampling import ReservoirSampling

class TriestImpr:
    def __init__(self, M):
        """
        Initialize TRIEST-IMPR (Algorithm 2).
        
        :param M: Fixed memory size (number of edges to store in sample).
        """
        self.M = M
        # The reservoir object handles the sampling logic and time 't'
        self.reservoir = ReservoirSampling(M)
        
        self.adj = defaultdict(set)
        self.global_triangles = 0.0 
        self.local_triangles = defaultdict(float)

    def get_common_neighbors(self, u, v):
        """Helper to find shared neighbors in the sampled graph (self.adj)."""
        if u in self.adj and v in self.adj:
            return self.adj[u].intersection(self.adj[v])
        return set()

    def process_edge(self, u, v):
        """
        TRIEST-IMPR Processing Logic.
        Updates counters unconditionally before sampling.
        """
        # Calculate the current time step 't'
        t = self.reservoir.t + 1
        
        # Unconditional Weighted Update
        # Calculate weight eta
        if t <= self.M:
            eta = 1.0
        else:
            eta = ((t - 1) * (t - 2)) / (self.M * (self.M - 1))
            eta = max(1.0, eta)

        # Update counters with the weight 'eta' BEFORE modifying the sample
        common = self.get_common_neighbors(u, v)
        for c in common:
            val = eta
            self.global_triangles += val
            self.local_triangles[u] += val
            self.local_triangles[v] += val
            self.local_triangles[c] += val

        # Reservoir Sampling Logic
        # We pass the edge to the reservoir logic
        added, removed_item = self.reservoir.add_item((u, v))

        # Handle Removal (IMPR does NOT decrement counters when removing)
        if removed_item:
            ru, rv = removed_item
            self.adj[ru].discard(rv)
            self.adj[rv].discard(ru)
            if not self.adj[ru]: del self.adj[ru]
            if not self.adj[rv]: del self.adj[rv]

        # Handle Addition (Update adjacency list)
        if added:
            self.adj[u].add(v)
            self.adj[v].add(u)

    def get_estimation(self):
        """
        Returns the global estimation. 
        [cite_start]For IMPR, the counter itself is the estimator[cite: 609].
        """
        return self.global_triangles