#!/usr/bin/env python3
import os
import csv
from time import time
from itertools import combinations
from collections import defaultdict
from multiprocessing import Pool, cpu_count

# =====================
# PARAMETERS
# =====================
DATA_PATH = "data/T10I4D100K.dat"
OUTPUT_CSV_ITEMSETS = "frequent_itemsets.csv"
OUTPUT_CSV_RULES = "association_rules.csv"

min_support_apriori = 1000  # min support count for Apriori
max_k = 3  # max size of frequent itemsets
min_support_rules = 1000  # min support count for rules
min_confidence = 0.6  # confidence threshold
top_n_rules_to_print = 30  # top rules to show


# =====================
# HELPER FUNCTIONS
# =====================
def load_transactions(path):
    """
       Load and parse transaction data from file.

       Args:
           path (str): Path to the data file

       Returns:
           list: List of transactions, each as sorted list of integers

       Raises:
           FileNotFoundError: If the specified path doesn't exist
       """

    transactions = []
    if not os.path.exists(path):
        raise FileNotFoundError(f"{path} not found.")
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            tokens = []
            cur = ""
            for ch in line:
                if ch.isdigit():
                    cur += ch
                else:
                    if cur:
                        tokens.append(cur)
                        cur = ""
            if cur:
                tokens.append(cur)
            try:
                items = frozenset(int(t) for t in tokens) if tokens else frozenset()
            except ValueError:
                parts = [p for p in line.split() if p.strip()]
                items = frozenset(int(p) for p in parts)
            if items:
                transactions.append(sorted(items))  # store sorted list for faster processing
    return transactions


def get_frequent_1_itemsets(transactions, min_support):
    """
        Find all frequent 1-itemsets from transactions.

        Args:
            transactions (list): List of transactions
            min_support (int): Minimum support count threshold

        Returns:
            dict: Dictionary of frequent 1-itemsets with their support counts
        """
    counts = defaultdict(int)
    for t in transactions:
        for item in t:
            counts[item] += 1
    L1 = {(item,): cnt for item, cnt in counts.items() if cnt >= min_support}
    return L1


def apriori_gen(Lk_minus_1, k):
    """
        Generate candidate itemsets of size k from frequent itemsets of size k-1.

        Args:
            Lk_minus_1 (dict): Frequent itemsets of size k-1
            k (int): Target itemset size

        Returns:
            set: Candidate itemsets of size k
        """
    prev_itemsets = sorted(Lk_minus_1.keys())
    candidates = set()
    len_prev = len(prev_itemsets)
    for i in range(len_prev):
        for j in range(i + 1, len_prev):
            a = prev_itemsets[i]
            b = prev_itemsets[j]
            if a[:k - 2] == b[:k - 2]:
                new_candidate = tuple(sorted(set(a) | set(b)))
                if len(new_candidate) == k:
                    if all(tuple(sorted(subset)) in Lk_minus_1 for subset in combinations(new_candidate, k - 1)):
                        candidates.add(new_candidate)
            else:
                break
    return candidates


def count_supports_fast(candidates, transactions):
    """
        Count support for candidate itemsets using efficient combination generation.

        Args:
            candidates (set): Candidate itemsets to count
            transactions (list): List of transactions

        Returns:
            dict: Support counts for each candidate itemset
        """
    k = len(next(iter(candidates))) if candidates else 0
    candidate_sets = set(map(frozenset, candidates))
    counts = defaultdict(int)
    for t in transactions:
        if len(t) >= k:
            for subset in combinations(t, k):
                fs = frozenset(subset)
                if fs in candidate_sets:
                    counts[tuple(sorted(fs))] += 1
    return counts


def parallel_count_supports(args):
    """
        Wrapper function for parallel support counting.

        Args:
            args (tuple): Tuple of (candidates_chunk, transactions)

        Returns:
            dict: Partial support counts for the chunk
        """
    candidates_chunk, transactions = args
    return count_supports_fast(candidates_chunk, transactions)


def count_supports_parallel(candidates, transactions):
    """
        Distribute support counting across multiple CPU cores.

        Args:
            candidates (set): All candidate itemsets
            transactions (list): List of transactions

        Returns:
            dict: Combined support counts from all processes
        """
    n_cpus = min(cpu_count(), 8)
    chunk_size = len(candidates) // n_cpus or 1
    chunks = [list(candidates)[i:i + chunk_size] for i in range(0, len(candidates), chunk_size)]
    with Pool(n_cpus) as pool:
        results = pool.map(parallel_count_supports, [(chunk, transactions) for chunk in chunks])
    final_counts = defaultdict(int)
    for r in results:
        for k, v in r.items():
            final_counts[k] += v
    return dict(final_counts)


def apriori(transactions, min_support, max_k=None):
    """
      Main Apriori algorithm to find all frequent itemsets.

      Args:
          transactions (list): List of transactions
          min_support (int): Minimum support count threshold
          max_k (int, optional): Maximum itemset size to mine

      Returns:
          dict: Dictionary containing frequent itemsets for each size k
      """

    frequent_itemsets = dict()
    L1 = get_frequent_1_itemsets(transactions, min_support)
    k = 1
    Lk = L1
    if Lk:
        frequent_itemsets[k] = Lk
    while Lk:
        k += 1
        if max_k and k > max_k:
            break
        candidates = apriori_gen(Lk, k)
        if not candidates:
            break
        counts = count_supports_parallel(candidates, transactions)
        Lk = {c: cnt for c, cnt in counts.items() if cnt >= min_support}
        if Lk:
            frequent_itemsets[k] = Lk
    return frequent_itemsets


# =====================
# GENERATE ASSOCIATION RULES
# =====================
def generate_association_rules(freq_itemsets, n_transactions, min_support, min_confidence):
    """
       Generate association rules from frequent itemsets.

       Args:
           freq_itemsets (dict): Frequent itemsets found by Apriori
           n_transactions (int): Total number of transactions
           min_support (int): Minimum support count for rules
           min_confidence (float): Minimum confidence threshold

       Returns:
           list: List of association rules sorted by confidence and support
       """

    support = {tuple(sorted(k)): v for k, v in
            [(itemset, sup) for d in freq_itemsets.values() for itemset, sup in d.items()]}
    rules = []
    for k, d in freq_itemsets.items():
        if k < 2:
            continue
        for itemset_tuple, sup_J in d.items():
            if sup_J < min_support:
                continue
            items = tuple(sorted(itemset_tuple))
            n_items = len(items)
            for r in range(1, n_items):
                for antecedent in combinations(items, r):
                    antecedent = tuple(sorted(antecedent))
                    consequent = tuple(sorted(set(items) - set(antecedent)))
                    sup_A = support.get(antecedent, 0)
                    if sup_A == 0:
                        continue
                    confidence = sup_J / sup_A
                    if confidence >= min_confidence:
                        sup_B = support.get(consequent, 0)
                        support_frac = sup_J / n_transactions
                        lift = (sup_J * n_transactions) / (sup_A * sup_B) if sup_B > 0 else None
                        rule = {
                            "antecedent": antecedent,
                            "consequent": consequent,
                            "support_count": sup_J,
                            "support_frac": support_frac,
                            "confidence": confidence,
                            "lift": lift,
                            "support_antecedent": sup_A,
                            "support_consequent": sup_B
                        }
                        rules.append(rule)
    rules_sorted = sorted(rules, key=lambda r: (-r["confidence"], -r["support_count"]))
    return rules_sorted


def save_rules_to_csv(rules, path):
    """
       Save association rules to CSV file.

       Args:
           rules (list): List of association rules to save
           path (str): Output file path
       """

    with open(path, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["antecedent", "consequent", "support_count", "support_frac",
                        "confidence", "lift", "support_antecedent", "support_consequent"])
        for r in rules:
            writer.writerow([
                " ".join(map(str, r["antecedent"])),
                " ".join(map(str, r["consequent"])),
                r["support_count"],
                f"{r['support_frac']:.6f}",
                f"{r['confidence']:.6f}",
                f"{r['lift']:.6f}" if r["lift"] is not None else "",
                r["support_antecedent"],
                r["support_consequent"]
            ])


# =====================
# MAIN EXECUTION
# =====================
if __name__ == "__main__":
    t0 = time()
    transactions = load_transactions(DATA_PATH)
    n_transactions = len(transactions)
    print(f"Loaded {n_transactions} transactions in {time() - t0:.2f}s")

    freq_itemsets = apriori(transactions, min_support_apriori, max_k=max_k)
    print(f"Apriori finished in {time() - t0:.2f}s")

    total_found = sum(len(d) for d in freq_itemsets.values())
    print(f"Total frequent itemsets found: {total_found}")
    for k in sorted(freq_itemsets):
        print(f" k={k}: {len(freq_itemsets[k])} itemsets")

    # Save frequent itemsets
    with open(OUTPUT_CSV_ITEMSETS, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["k", "itemset", "support"])
        for k in sorted(freq_itemsets):
            for itemset, sup in freq_itemsets[k].items():
                writer.writerow([k, " ".join(map(str, itemset)), sup])
    print(f"Written frequent itemsets to {OUTPUT_CSV_ITEMSETS}")

    # Generate association rules
    rules = generate_association_rules(freq_itemsets, n_transactions,
                                    min_support_rules, min_confidence)
    print(f"Generated {len(rules)} rules (min_support={min_support_rules}, min_confidence={min_confidence})")

    to_show = min(len(rules), top_n_rules_to_print)
    if to_show > 0:
        print(f"\nTop {to_show} rules:")
        for i, r in enumerate(rules[:to_show], 1):
            ant = " ".join(map(str, r["antecedent"]))
            con = " ".join(map(str, r["consequent"]))
            lift_str = f"{r['lift']:.3f}" if r['lift'] is not None else "N/A"
            print(f"{i:2d}. {ant} -> {con}    sup={r['support_count']} ({r['support_frac']:.4f})  "
                f"conf={r['confidence']:.3f}  lift={lift_str}")

    # Save rules CSV
    save_rules_to_csv(rules, OUTPUT_CSV_RULES)
    print(f"Saved rules to {OUTPUT_CSV_RULES}")
