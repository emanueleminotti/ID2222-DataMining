from typing import List

class CompareSignatures:
    """
    Estimates Jaccard similarity by comparing MinHash signatures.
    """

    @staticmethod
    def calculate_similarity(sig_a: List[int], sig_b: List[int]) -> float:
        """
        Estimates the Jaccard similarity of the original sets by comparing their MinHash signatures.
        The similarity is the fraction of signature components that are equal.

        Args:
            sig_a (List[int]): The MinHash signature for set A.
            sig_b (List[int]): The MinHash signature for set B.

        Returns:
            float: The estimated Jaccard similarity (0.0 to 1.0).
        """
        if len(sig_a) != len(sig_b):
            raise ValueError("Signatures must be of the same length to be compared")
        
        if len(sig_a) == 0:
            # By definition, two empty sets are 100% similar
            return 1.0  

        # Count the number of components that match
        matches = 0
        for i in range(len(sig_a)):
            if sig_a[i] == sig_b[i]:
                matches += 1
        
        # The estimate is the fraction of matching components
        return matches / len(sig_a)

# -----------------------------------------------------------------
# Test block
# -----------------------------------------------------------------
if __name__ == "__main__":
    sig1 = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    sig2 = [10, 99, 30, 40, 99, 60, 99, 80, 90, 99]

    estimated_sim = CompareSignatures.calculate_similarity(sig1, sig2)
    
    print(f"\nSignature 1: {sig1}")
    print(f"Signature 2: {sig2}")
    print(f"\nSignature Length: {len(sig1)}")
    print(f"Estimated Jaccard Similarity: {estimated_sim:.4f} (Expected: 0.6)")