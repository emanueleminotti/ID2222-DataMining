from typing import Iterable

class CompareSets:
    """
    Computes the Jaccard similarity of two sets of integers.
    """

    @staticmethod
    def calculate_jaccard(a: Iterable[int], b: Iterable[int]) -> float:
        """
        Computes the Jaccard similarity between two iterables of integers.
        J(A, B) = |A ∩ B| / |A ∪ B|

        Args:
            a (Iterable[int]): The first set/list of items.
            b (Iterable[int]): The second set/list of items.

        Returns:
            float: The Jaccard similarity (0.0 to 1.0).
        """
        # Convert iterables to sets for efficient intersection/union
        set_a = set(a)
        set_b = set(b)

        # Get lengths of intersection and union using set operators
        intersection_len = len(set_a & set_b)
        union_len = len(set_a | set_b)

        # Handle division by zero if union is empty
        if union_len == 0:
            return 1.0  # Two empty sets are considered 100% similar

        return intersection_len / union_len

# -----------------------------------------------------------------
# Test block
# -----------------------------------------------------------------
if __name__ == "__main__":
    set1 = {1, 2, 3, 4, 5}
    set2 = {4, 5, 6, 7, 8}

    sim1 = CompareSets.calculate_jaccard(set1, set2)
    print(f"\nJaccard Similarity: {sim1:.4f} (Expected: 0.25)")