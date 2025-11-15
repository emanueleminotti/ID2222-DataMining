import random

class ReservoirSampling:
    def __init__(self, memory_size):
        """
        Initializes the Reservoir Sampler.
        
        :param memory_size: The fixed size M of the reservoir.
        """
        self.M = memory_size
        self.sample = [] # Stores the actual elements (edges)
        self.t = 0       # The number of items seen so far

    def add_item(self, item):
        """
        Processes an item (e.g., an edge) using the Reservoir Sampling algorithm.
        
        Returns a tuple: (added, removed_item)
        - added: Boolean, True if the new item was added to the sample.
        - removed_item: The item that was removed to make space, or None if no item was removed.
        """
        self.t += 1

        # Fill the reservoir up to M
        if len(self.sample) < self.M:
            self.sample.append(item)
            # Item added, nothing removed
            return True, None

        # Random replacement with probability M/t
        if random.random() < (self.M / self.t):
            # Pick a random index to evict
            idx = random.randint(0, self.M - 1)
            removed_item = self.sample[idx]
            
            # Replace the element
            self.sample[idx] = item
            
            # Item added, old item removed
            return True, removed_item

        # Item was skipped
        return False, None