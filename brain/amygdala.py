"""
amygdala.py — LeDoux 1996
==========================
Fear / salience conditioning. 低路徑: thalamus→amygdala (快, 粗)；
高路徑: thalamus→cortex→amygdala (慢, 精細)。
"""
from __future__ import annotations
import random
try:
    import numpy as _np; _HAS_NP = True
except Exception: _HAS_NP = False


class Amygdala:
    def __init__(self, n_in=64, eta=0.05, seed=0):
        self.n = n_in; self.eta = eta
        rng = random.Random(seed)
        if _HAS_NP:
            self.w = _np.zeros(n_in, _np.float32)
        else:
            self.w = [0.0]*n_in
        self.arousal = 0.0   # 0..1

    def evaluate(self, features):
        """回 (valence, arousal)，valence in [-1,1]"""
        if _HAS_NP:
            v = float((_np.asarray(features, _np.float32) * self.w).sum())
        else:
            v = sum(f*w for f,w in zip(features, self.w))
        # squash
        val = 2.0/(1.0+pow(2.718281828,-v)) - 1.0
        self.arousal = min(1.0, abs(val))
        return val, self.arousal

    def condition(self, features, outcome_valence):
        """關聯：features 共現 negative outcome → w 變負。"""
        if _HAS_NP:
            f = _np.asarray(features, _np.float32)
            self.w += self.eta * outcome_valence * f
            _np.clip(self.w, -5.0, 5.0, out=self.w)
        else:
            for i,f in enumerate(features):
                self.w[i] += self.eta*outcome_valence*f
                if self.w[i] > 5: self.w[i] = 5
                elif self.w[i] < -5: self.w[i] = -5
