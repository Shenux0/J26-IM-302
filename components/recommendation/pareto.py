"""Pareto (non-dominated) filtering over fix candidates."""
from __future__ import annotations

import numpy as np


def pareto_front(matrix: np.ndarray, benefit: np.ndarray) -> np.ndarray:
    """Boolean mask of rows that no other row dominates.

    ``matrix`` is (alternatives × criteria); ``benefit[j]`` is True when higher is
    better for criterion j and False for cost criteria.
    """
    x = np.asarray(matrix, dtype=float)
    x = np.where(np.asarray(benefit, dtype=bool), x, -x)  # make every criterion "maximise"
    mask = np.ones(len(x), dtype=bool)
    for i in range(len(x)):
        dominated_by = np.all(x >= x[i], axis=1) & np.any(x > x[i], axis=1)
        mask[i] = not dominated_by.any()
    return mask
