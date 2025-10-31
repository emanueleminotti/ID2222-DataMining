import zlib
from typing import List

class Shingling:
    """
    Constructs k-shingles from a document, hashes them, and returns an ordered set of unique hash values.
    """

    def __init__(self, k: int):
        """
        Initializes the shingler with a shingle length k.

        Args:
            k (int): The length of the k-shingles.
        """
        if not isinstance(k, int) or k <= 0:
            raise ValueError("k must be a positive integer")
        self.k = k

    def get_hashed_shingles(self, doc_text: str) -> List[int]:
        """
        Processes a document into a sorted list of its unique hashed k-shingles.

        Args:
            doc_text (str): The input document text.

        Returns:
            List[int]: A sorted list of unique 32-bit hashed shingle values.
        """
        if not isinstance(doc_text, str):
            raise TypeError("Input document must be a string.")

        if len(doc_text) < self.k:
            return []  # Not enough text to create any shingles

        # Set to store unique hashed shingles
        hashed_shingles_set = set()

        # Iterate through the document and create shingles
        for i in range(len(doc_text) - self.k + 1):
            # Get the k-shingle
            shingle = doc_text[i : i + self.k]

            # Hash the shingle
            shingle_bytes = shingle.encode('utf-8')

            hash_val = zlib.crc32(shingle_bytes) & 0xffffffff
            
            # Add the unique hash to the set
            hashed_shingles_set.add(hash_val)

        # Return an "ordered set" (a sorted list)
        return sorted(list(hashed_shingles_set))

# -----------------------------------------------------------------
# Test block
# -----------------------------------------------------------------
if __name__ == "__main__":
    k = 3
    shingler = Shingling(k=k)

    doc1 = "abcde"
    doc2 = "bcdef"

    shingles1 = shingler.get_hashed_shingles(doc1)
    shingles2 = shingler.get_hashed_shingles(doc2)

    print(f"\n--- (k={k}) ---")
    print(f"Doc 1 ('{doc1}'): {shingles1}")
    print(f"Doc 2 ('{doc2}'): {shingles2}")

    # Calculate Jaccard Similarity
    s1 = set(shingles1)
    s2 = set(shingles2)
    
    jaccard_sim = len(s1.intersection(s2)) / len(s1.union(s2))
    
    print(f"Jaccard Similarity: {jaccard_sim:.4f} (Expected: 0.5)")