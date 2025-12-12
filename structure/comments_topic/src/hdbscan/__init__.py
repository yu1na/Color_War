from __future__ import annotations

from typing import Optional

import numpy as np
from sklearn.cluster import KMeans


class HDBSCAN:
    def __init__(
        self,
        n_clusters: Optional[int] = None,
        random_state: int = 42,
        **_: object,
    ) -> None:
        self.n_clusters = n_clusters
        self.random_state = random_state

    def fit(self, X: np.ndarray, y: Optional[np.ndarray] = None) -> "HDBSCAN":
        sample_count = X.shape[0]
        k = self.n_clusters or max(2, min(12, sample_count // 500 + 2))
        model = KMeans(n_clusters=k, random_state=self.random_state, n_init="auto")
        model.fit(X)
        self.labels_ = model.labels_
        return self

    def fit_predict(self, X: np.ndarray, y: Optional[np.ndarray] = None) -> np.ndarray:
        return self.fit(X, y).labels_


__all__ = ["HDBSCAN"]
