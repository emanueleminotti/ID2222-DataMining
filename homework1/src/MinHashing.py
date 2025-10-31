import random
from typing import List, Iterable, Set

class MinHashing:
    """
    Creates MinHash signatures from sets of hashed shingles using universal hashing.
    """

    # A large prime number slightly larger than 2**32 (our max shingle hash)
    # This is our 'p' for the (a*x + b) % p hash function.
    MOD_PRIME = 4294967311 

    def __init__(self, num_hashes: int, seed: int = 42):
        """
        Initializes the MinHasher by generating coefficients for 'num_hashes' different hash functions.

        Args:
            num_hashes (int): The number of hash functions (signature length).
            seed (int): A seed for the random number generator to ensure
                        the same hash functions are generated every time.
        """
        if not isinstance(num_hashes, int) or num_hashes <= 0:
            raise ValueError("num_hashes must be a positive integer")

        self.num_hashes = num_hashes
        
        # Use a consistent, seeded random generator.
        rng = random.Random(seed)

        # Generate 'num_hashes' pairs of (a, b) coefficients
        self.hash_coeffs = []
        for _ in range(self.num_hashes):
            # a and b are random integers in [1, MOD_PRIME - 1]
            a = rng.randint(1, self.MOD_PRIME - 1)
            b = rng.randint(1, self.MOD_PRIME - 1)
            self.hash_coeffs.append((a, b))

    def get_signature(self, hashed_shingles: Iterable[int]) -> List[int]:
        """
        Computes the MinHash signature for a set of hashed shingles.

        Args:
            hashed_shingles (Iterable[int]): A set or list of hashed shingles.

        Returns:
            List[int]: The MinHash signature (a list of length num_hashes).
        """
        
        # Initialize the signature vector with infinity
        signature: List[float] = [float('inf')] * self.num_hashes

        # We only need to iterate over the unique shingles
        shingles_set: Set[int] = set(hashed_shingles)

        if not shingles_set:
            # Return a default signature for empty sets
            return [0] * self.num_hashes 

        # For each unique shingle apply 'num_hashes' hash functions
        for shingle_hash in shingles_set:
            for i in range(self.num_hashes):
                a, b = self.hash_coeffs[i]
                
                # Compute the hash: h(x) = (a*x + b) % p
                hash_val = (a * shingle_hash + b) % self.MOD_PRIME

                # Update the signature if this is the new minimum value found for this hash function
                signature[i] = min(signature[i], hash_val)
        
        # Convert from float('inf') to int for the final signature
        return [int(s) for s in signature]

# -----------------------------------------------------------------
# Test block
# -----------------------------------------------------------------
if __name__ == "__main__":
    # --- Example: Compare two sets ---

    set1 = {1, 2, 3, 4, 5}
    set2 = {4, 5, 6, 7, 8}

    # 1. Calculate the true Jaccard similarity
    s1 = set(set1)
    s2 = set(set2)
    true_jaccard = len(s1.intersection(s2)) / len(s1.union(s2))
    
    print(f"\nSet 1: {set1}")
    print(f"Set 2: {set2}")
    print(f"True Jaccard Similarity: {true_jaccard:.4f}")

    # 2. Calculate the MinHash Signatures
    num_hashes = 200
    min_hasher = MinHashing(num_hashes=num_hashes)

    sig1 = min_hasher.get_signature(set1)
    sig2 = min_hasher.get_signature(set2)

    print(f"\nGenerated {num_hashes} MinHash signatures.")
    print(f"Sig 1 (first 10): {sig1[:10]}...")
    print(f"Sig 2 (first 10): {sig2[:10]}...")

    # 3. Estimate Jaccard Similarity from signatures
    # The probability that sig1[i] == sig2[i] is the Jaccard similarity
    matching_hashes = 0
    for i in range(num_hashes):
        if sig1[i] == sig2[i]:
            matching_hashes += 1
            
    estimated_jaccard = matching_hashes / num_hashes
    
    print(f"\nEstimated Jaccard from Signatures: {estimated_jaccard:.4f}")
    print(f"Difference (Error): {abs(true_jaccard - estimated_jaccard):.4f}")