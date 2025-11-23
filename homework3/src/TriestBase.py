import random
from collections import defaultdict
from src.ReservoirSampling import ReservoirSampling

class TriestBase:
    def __init__(self, M):
        """
        Initialize TRIEST-BASE (Algorithm 1).
        
        :param M: Fixed memory size (number of edges to store in sample).
        """
        self.M = M
        # The reservoir object now manages the sample and its own time 't'
        self.reservoir = ReservoirSampling(M)
        
        # Adjacency list for the *sampled* graph
        self.adj = defaultdict(set) 
        
        # Counters for sampled triangles
        self.global_triangles = 0
        self.local_triangles = defaultdict(int)

    def get_common_neighbors(self, u, v):
        """Helper to find shared neighbors in the sampled graph (self.adj)."""
        if u in self.adj and v in self.adj:
            return self.adj[u].intersection(self.adj[v])
        return set()

    def update_counters(self, u, v, is_addition=True):
        """Updates global and local counters based on common neighbors in S."""
        common = self.get_common_neighbors(u, v)
        change = 1 if is_addition else -1
        
        for c in common:
            self.global_triangles += change
            self.local_triangles[u] += change
            self.local_triangles[v] += change
            self.local_triangles[c] += change

    def process_edge(self, u, v):
        """
        Main stream processing loop.
        Feeds the new edge to the reservoir and updates graph state accordingly.
        """
        edge = (u, v)
        
        # The reservoir's internal time 't' is incremented here
        added, removed_item = self.reservoir.add_item(edge)

        # Handle edge removal (if reservoir was full and kicked one out)
        if removed_item:
            ru, rv = removed_item
            
            # Decrement counters for the removed edge
            # This is the "UPDATE COUNTERS(-, (u', v'))" step
            self.update_counters(ru, rv, is_addition=False)
            
            # Remove from adjacency list
            self.adj[ru].discard(rv)
            self.adj[rv].discard(ru)
            if not self.adj[ru]: del self.adj[ru]
            if not self.adj[rv]: del self.adj[rv]

        # Handle edge addition (if the new edge was kept)
        if added:
            # Increment counters for the new edge
            # This is the "UPDATE COUNTERS(+, (u, v))" step
            self.update_counters(u, v, is_addition=True)
            
            # Add to adjacency list
            self.adj[u].add(v)
            self.adj[v].add(u)

    def get_estimation(self):
        """
        Returns the estimated global triangle count.
        Formula: xi * tau.
        """
        # Get the current time 't' from the reservoir object
        t = self.reservoir.t
        
        if t <= self.M:
            return self.global_triangles
        
        # Ensure M is large enough for the formula
        if self.M < 3:
            return 0 # Cannot estimate with M < 3

        # Scaling factor xi
        xi = (t * (t - 1) * (t - 2)) / (self.M * (self.M - 1) * (self.M - 2))
        return xi * self.global_triangles