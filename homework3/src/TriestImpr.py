import random
from collections import defaultdict

class TriestImpr:
    def __init__(self, M):
        self.M = M
        self.S = set()
        self.adj = defaultdict(set)
        self.global_triangles = 0.0 # Float for weighted updates
        self.local_triangles = defaultdict(float)
        self.t = 0

    def get_common_neighbors(self, u, v):
        if u in self.adj and v in self.adj:
            return self.adj[u].intersection(self.adj[v])
        return set()

    def process_edge(self, u, v):
        """
        TRIEST-IMPR Processing.
        """
        self.t += 1
        
        # 1. Unconditional Weighted Update
        # Calculate weight eta 
        if self.t <= self.M:
            eta = 1.0
        else:
            eta = ((self.t - 1) * (self.t - 2)) / (self.M * (self.M - 1))
            eta = max(1.0, eta)

        common = self.get_common_neighbors(u, v)
        for c in common:
            val = eta
            self.global_triangles += val
            self.local_triangles[u] += val
            self.local_triangles[v] += val
            self.local_triangles[c] += val

        # 2. Reservoir Sampling Logic
        # Note: IMPR does NOT decrement counters when removing from S
        if self.t <= self.M:
            self.S.add((u, v))
            self.adj[u].add(v)
            self.adj[v].add(u)
        elif random.random() < (self.M / self.t):
            # Replace random edge
            remove_edge = random.choice(list(self.S))
            self.S.remove(remove_edge)
            ru, rv = remove_edge
            self.adj[ru].remove(rv)
            self.adj[rv].remove(ru)
            if not self.adj[ru]: del self.adj[ru]
            if not self.adj[rv]: del self.adj[rv]

            # Add new edge
            self.S.add((u, v))
            self.adj[u].add(v)
            self.adj[v].add(u)

    def get_estimation(self):
        """Returns the global estimation. For IMPR, this is just the counter value."""
        return self.global_triangles