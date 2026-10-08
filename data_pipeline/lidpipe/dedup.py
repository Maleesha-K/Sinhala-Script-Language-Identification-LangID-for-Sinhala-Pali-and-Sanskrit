"""Near-duplicate detection: MinHash LSH over character shingles, verified by
exact Jaccard (Broder 1997; Lee et al. 2022, "Deduplicating Training Data")."""
from datasketch import MinHash, MinHashLSH


def shingles(text, k):
    text = text.replace(' ', '_')
    return {text[i:i + k] for i in range(max(1, len(text) - k + 1))}


def jaccard(a, b):
    return len(a & b) / len(a | b) if a or b else 1.0


def near_duplicate_pairs(texts, k=5, num_perm=128, threshold=0.8):
    """Return sorted (i, j) index pairs, i < j, with Jaccard(shingles) >= threshold.

    LSH proposes candidates; each candidate is confirmed with the exact Jaccard,
    so the result has no false positives (false negatives are possible, as with
    any LSH, and are reported via the verification pass in the callers).
    """
    sets = [shingles(t, k) for t in texts]
    lsh = MinHashLSH(threshold=threshold, num_perm=num_perm)
    sigs = []
    for i, s in enumerate(sets):
        m = MinHash(num_perm=num_perm, seed=1)
        m.update_batch([g.encode('utf-8') for g in s])
        lsh.insert(i, m)
        sigs.append(m)
    pairs = set()
    for i, m in enumerate(sigs):
        for j in lsh.query(m):
            if j > i and jaccard(sets[i], sets[j]) >= threshold:
                pairs.add((i, j))
    return sorted(pairs)


def near_matches(queries, references, k=5, num_perm=128, threshold=0.8):
    """Indices of `queries` that have a near-duplicate (Jaccard >= threshold)
    in `references`. Used to decontaminate training data against test sets."""
    ref_sets = [shingles(t, k) for t in references]
    lsh = MinHashLSH(threshold=threshold, num_perm=num_perm)
    for i, s in enumerate(ref_sets):
        m = MinHash(num_perm=num_perm, seed=1)
        m.update_batch([g.encode('utf-8') for g in s])
        lsh.insert(i, m)
    hits = set()
    for qi, text in enumerate(queries):
        s = shingles(text, k)
        m = MinHash(num_perm=num_perm, seed=1)
        m.update_batch([g.encode('utf-8') for g in s])
        if any(jaccard(s, ref_sets[r]) >= threshold for r in lsh.query(m)):
            hits.add(qi)
    return hits


def clusters(n, pairs):
    """Union-find over `pairs`; returns a representative index for each item
    (the smallest index in its cluster)."""
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for i, j in pairs:
        a, b = find(i), find(j)
        if a != b:
            parent[max(a, b)] = min(a, b)
    return [find(i) for i in range(n)]
