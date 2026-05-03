"""
predictive.py — Rao & Ballard 1999 / Friston FEP / Clark 2013
==============================================================
Hierarchical predictive coding: 每層預測下一層活動；只傳 prediction error 往上。
"""
from __future__ import annotations
try:
    import numpy as _np; _HAS_NP = True
except Exception: _HAS_NP = False


class PredictiveLayer:
    def __init__(self, n_low, n_high, eta=0.01, seed=0):
        if not _HAS_NP:
            raise RuntimeError("PredictiveLayer needs numpy (fallback 留給 rate-only)")
        rs = _np.random.RandomState(seed)
        self.W = (0.1*rs.randn(n_high, n_low)).astype(_np.float32)
        self.r = _np.zeros(n_high, _np.float32)
        self.eta = eta

    def infer(self, bottom, steps=5, lr=0.1):
        """給 bottom，迭代 r 讓 Wr ≈ bottom。回 (r, error)"""
        for _ in range(steps):
            pred = self.r @ self.W
            err  = bottom - pred
            self.r += lr * (err @ self.W.T)
        pred = self.r @ self.W
        err  = bottom - pred
        return self.r.copy(), err

    def learn(self, bottom, err):
        """更新 W 減少 error。"""
        self.W += self.eta * _np.outer(self.r, err)


class PredictiveHierarchy:
    def __init__(self, dims, seed=0):
        """dims = [d0, d1, d2, ...] 每層維度"""
        self.layers = []
        for i in range(len(dims)-1):
            self.layers.append(PredictiveLayer(dims[i], dims[i+1], seed=seed+i))

    def step(self, x, infer_steps=3):
        if not _HAS_NP:
            return x, 0.0
        v = _np.asarray(x, _np.float32)
        total_err = 0.0
        for layer in self.layers:
            r, err = layer.infer(v, steps=infer_steps)
            layer.learn(v, err)
            total_err += float((err*err).sum())
            v = r
        return v, total_err   # (top-level representation, free-energy proxy)
