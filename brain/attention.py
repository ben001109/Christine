"""
attention.py — Posner 1980 / Corbetta-Shulman 2002
===================================================
Top-down (endogenous) + bottom-up (exogenous) attention 整合成 saliency map。
"""
from __future__ import annotations
try: import numpy as _np; _HAS_NP=True
except Exception: _HAS_NP=False

class Attention:
    def __init__(self, n=64):
        self.n = n
        if _HAS_NP:
            self.saliency = _np.zeros(n, _np.float32)
            self.topdown  = _np.ones(n, _np.float32)
        else:
            self.saliency = [0.0]*n; self.topdown = [1.0]*n

    def update(self, bottom_up, top_down=None, alpha=0.5):
        if _HAS_NP:
            bu = _np.asarray(bottom_up, _np.float32)
            if len(bu) < self.n: bu = _np.pad(bu, (0, self.n-len(bu)))
            elif len(bu) > self.n: bu = bu[:self.n]
            if top_down is not None:
                td = _np.asarray(top_down, _np.float32)
                if len(td) < self.n: td = _np.pad(td, (0, self.n-len(td)), constant_values=1.0)
                elif len(td) > self.n: td = td[:self.n]
                self.topdown = td
            self.saliency = alpha*bu*self.topdown + (1-alpha)*self.saliency
            return self.saliency.copy()
        bu = list(bottom_up)
        if len(bu) < self.n: bu = bu + [0.0]*(self.n-len(bu))
        else: bu = bu[:self.n]
        if top_down:
            td = list(top_down)
            if len(td) < self.n: td = td + [1.0]*(self.n-len(td))
            else: td = td[:self.n]
            self.topdown = td
        for i in range(self.n):
            self.saliency[i] = alpha*bu[i]*self.topdown[i] + (1-alpha)*self.saliency[i]
        return list(self.saliency)

    def focus(self, k=3):
        """回最亮的 k 個 index。"""
        if _HAS_NP:
            return _np.argsort(self.saliency)[-k:][::-1].tolist()
        idx = sorted(range(self.n), key=lambda i: self.saliency[i], reverse=True)
        return idx[:k]
