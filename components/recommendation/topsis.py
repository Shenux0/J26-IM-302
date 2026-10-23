"""TOPSIS ranking (Technique for Order of Preference by Similarity to Ideal Solution)."""
from __future__ import annotations

import numpy as np


def topsis(matrix: np.ndarray, weights: np.ndarray, benefit: np.ndarray) -> np.ndarray:
    """Closeness to the ideal solution in [0, 1] for each row (1 = best).

    ``matrix`` is (alternatives × criteria), ``weights`` one per criterion (normalised
    here), ``benefit[j]`` True when higher is better. When no criterion varies across
    rows (e.g. a single candidate) every row scores 1.0.
    """
    x = np.asarray(matrix, dtype=float)
    if x.size == 0:
        return np.zeros(len(x))
    w = np.asarray(weights, dtype=float)
    benefit = np.asarray(benefit, dtype=bool)

    norm = np.linalg.norm(x, axis=0)
    norm[norm == 0] = 1.0
    v = x / norm * (w / w.sum())

    ideal = np.where(benefit, v.max(axis=0), v.min(axis=0))
    anti_ideal = np.where(benefit, v.min(axis=0), v.max(axis=0))
    d_best = np.linalg.norm(v - ideal, axis=1)
    d_worst = np.linalg.norm(v - anti_ideal, axis=1)
    total = d_best + d_worst
    return np.divide(d_worst, total, out=np.ones_like(d_worst), where=total > 0)
