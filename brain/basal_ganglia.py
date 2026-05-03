"""
basal_ganglia.py — Doya 1999 / Houk-Adams-Barto 1995
====================================================
Actor-critic with TD-learning. Striatum = actor; dopamine = δ = TD error.
"""
from __future__ import annotations
import random

try:
    import numpy as _np
    _HAS_NP = True
except Exception:
    _HAS_NP = False


class BasalGanglia:
    def __init__(self, n_state=64, n_action=8, alpha=0.05, gamma=0.9, seed=0):
        self.ns=n_state; self.na=n_action; self.alpha=alpha; self.gamma=gamma
        rng = random.Random(seed)
        if _HAS_NP:
            rs = _np.random.RandomState(seed)
            self.V = _np.zeros(n_state, _np.float32)     # critic
            self.A = (0.01*rs.randn(n_state, n_action)).astype(_np.float32)  # actor
        else:
            self.V = [0.0]*n_state
            self.A = [[rng.gauss(0,0.01) for _ in range(n_action)] for _ in range(n_state)]
        self.prev_state = None; self.prev_action = None
        self.dopamine = 0.0    # τ TD error

    def _softmax_action(self, s_idx):
        if _HAS_NP:
            logits = self.A[s_idx]
            e = _np.exp(logits - logits.max()); p = e/e.sum()
            return int(_np.random.choice(self.na, p=p))
        row = self.A[s_idx]
        m = max(row); exps = [pow(2.718281828, r-m) for r in row]
        s = sum(exps); probs = [e/s for e in exps]
        r = random.random(); acc = 0.0
        for i,p in enumerate(probs):
            acc += p
            if r <= acc: return i
        return self.na-1

    def act(self, state_idx):
        """state_idx: int in [0, ns). 回 action int."""
        a = self._softmax_action(state_idx)
        self.prev_state = state_idx; self.prev_action = a
        return a

    def learn(self, reward, new_state_idx):
        """TD: δ = r + γV(s') − V(s)。更新 critic + actor。"""
        if self.prev_state is None: return 0.0
        s, a = self.prev_state, self.prev_action
        if _HAS_NP:
            delta = reward + self.gamma*self.V[new_state_idx] - self.V[s]
            self.V[s] += self.alpha*delta
            self.A[s,a] += self.alpha*delta
        else:
            delta = reward + self.gamma*self.V[new_state_idx] - self.V[s]
            self.V[s] += self.alpha*delta
            self.A[s][a] += self.alpha*delta
        self.dopamine = float(delta)
        return float(delta)
