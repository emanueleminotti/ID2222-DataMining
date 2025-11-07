import zlib
from typing import List, Set, Dict, Any, Tuple
from itertools import combinations

class LSH:
    """
    Implements Locality-Sensitive Hashing (LSH) for MinHash signatures to find candidate pairs of similar documents.
    """

    def __init__(self, num_bands: int, num_hashes: int):
        """
        Initializes the LSH index.

        Args:
            num_bands (int): The number of bands ('b') to split the signature into.
            num_hashes (int): The total length of the MinHash signatures ('n').
        
        Raises:
            ValueError: If num_hashes is not perfectly divisible by num_bands.
        """
        if num_hashes % num_bands != 0:
            raise ValueError("Total number of hashes (n) must be divisible by num_bands (b)")
        
        self.num_bands = num_bands
        self.num_hashes = num_hashes
        self.rows_per_band = num_hashes // num_bands
        
        self.hash_tables: List[Dict[int, List[Any]]] = [dict() for _ in range(self.num_bands)]
        
        print(f"  Total Hashes (n): {self.num_hashes}")
        print(f"  Bands (b): {self.num_bands}")
        print(f"  Rows per Band (r): {self.rows_per_band}")

    def add_signature(self, doc_id: Any, signature: List[int]):
        """
        Adds a single document's signature to the LSH index.

        The document is hashed into 'b' different buckets, one for each band.

        Args:
            doc_id (Any): A unique identifier for the document.
            signature (List[int]): The MinHash signature (must be length 'n').
        
        Raises:
            ValueError: If the signature length does not match self.num_hashes.
        """
        if len(signature) != self.num_hashes:
            raise ValueError(f"Signature length {len(signature)} does not match "
                            f"expected num_hashes {self.num_hashes}")
        
        for b in range(self.num_bands):
            # 1. Get the slice of the signature for the current band
            start_row = b * self.rows_per_band
            end_row = start_row + self.rows_per_band
            band: List[int] = signature[start_row:end_row]

            # 2. Hash the band content to a single bucket key.
            band_bytes = str(band).encode('utf-8')
            bucket_hash = zlib.crc32(band_bytes) & 0xffffffff

            # 3. Add the doc_id to the appropriate bucket in the correct band's table
            hash_table = self.hash_tables[b]
            
            if bucket_hash not in hash_table:
                hash_table[bucket_hash] = [doc_id]
            else:
                if doc_id not in hash_table[bucket_hash]:
                    hash_table[bucket_hash].append(doc_id)

    def get_candidate_pairs(self) -> Set[Tuple[Any, Any]]:
        """
        Finds all candidate pairs after all signatures have been added.

        A pair is a candidate if it appears in the same bucket in at least one band.

        Returns:
            Set[Tuple[Any, Any]]: A set of unique candidate pairs.
            Each pair is sorted to avoid duplicates.
        """
        candidate_pairs: Set[Tuple[Any, Any]] = set()

        # Iterate through each band's hash table
        for table in self.hash_tables:
            # Iterate through all buckets in the table
            for bucket in table.values():
                # If a bucket has 2 or more docs, they are candidates
                if len(bucket) > 1:
                    for pair in combinations(bucket, 2):
                        # Sort the pair so (doc_A, doc_B) is the same as (doc_B, doc_A)
                        sorted_pair = tuple(sorted(pair))
                        candidate_pairs.add(sorted_pair)
        
        return candidate_pairs
