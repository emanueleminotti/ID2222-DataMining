import random
from collections import defaultdict

class TriestBase:
    def __init__(self, M):
        """
        Initialize TRIEST-BASE.
        :param M: Fixed memory size (number of edges to store in sample).
        """
        self.M = M
        self.S = set()          # The reservoir sample of edges
        self.adj = defaultdict(set) # Adjacency list of S for fast lookup
        self.global_triangles = 0
        self.local_triangles = defaultdict(int)
        self.t = 0              # Time step (total edges seen)

    def get_common_neighbors(self, u, v):
        """Helper to find shared neighbors in the sample."""
        if u in self.adj and v in self.adj:
            return self.adj[u].intersection(self.adj[v])
        return set()

    def sample_edge(self, u, v, t):
        """
        Implementation of Reservoir Sampling [cite: 539-542].
        Returns True if the edge is added to the sample, False otherwise.
        """
        if t <= self.M:
            return True
        elif random.random() < (self.M / t):
            # Remove a random edge from S to make room
            remove_edge = random.choice(list(self.S))
            self.S.remove(remove_edge)
            
            # Update Adjacency List (Remove old edge)
            ru, rv = remove_edge
            self.adj[ru].remove(rv)
            self.adj[rv].remove(ru)
            
            # Cleanup empty adjacency entries to save memory
            if not self.adj[ru]: del self.adj[ru]
            if not self.adj[rv]: del self.adj[rv]
            
            # Update counters for REMOVAL (Specific to BASE)
            self.update_counters(ru, rv, is_addition=False)
            return True
        return False

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
        """Main stream processing loop."""
        self.t += 1
        
        # 1. Reservoir Sampling Logic
        if self.sample_edge(u, v, self.t):
            # 2. Add new edge to Sample and Adjacency List
            self.S.add((u, v))
            self.adj[u].add(v)
            self.adj[v].add(u)
            
            # 3. Update counters for ADDITION 
            self.update_counters(u, v, is_addition=True)

    def get_estimation(self):
        """
        Returns the estimated global triangle count.
        Formula: xi * tau.
        """
        if self.t <= self.M:
            return self.global_triangles
        
        xi = (self.t * (self.t - 1) * (self.t - 2)) / (self.M * (self.M - 1) * (self.M - 2))
        return xi * self.global_triangles