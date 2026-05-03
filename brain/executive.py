"""
executive.py — Miller-Cohen 2001 PFC / Norman-Shallice SAS
============================================================
Working memory slots + goal stack + conflict monitoring (Botvinick)。
"""
from __future__ import annotations
import time

class Executive:
    def __init__(self, wm_slots=4):
        self.wm = []                 # [(content, strength)]
        self.goals = []              # stack
        self.conflict = 0.0
        self.wm_slots = wm_slots

    def push_goal(self, g): self.goals.append(g)
    def pop_goal(self):
        return self.goals.pop() if self.goals else None
    def current_goal(self):
        return self.goals[-1] if self.goals else None

    def wm_write(self, item, strength=1.0):
        self.wm.append([item, float(strength), time.time()])
        if len(self.wm) > self.wm_slots:
            self.wm.sort(key=lambda x: x[1], reverse=True)
            self.wm = self.wm[:self.wm_slots]

    def wm_read(self):
        return [w[0] for w in self.wm]

    def detect_conflict(self, options_scores):
        """Botvinick conflict = − Σ p log p (normalised)"""
        import math
        if not options_scores: self.conflict = 0.0; return 0.0
        mx = max(options_scores); exps = [math.exp(s-mx) for s in options_scores]
        tot = sum(exps); probs = [e/tot for e in exps]
        ent = -sum(p*math.log(p+1e-9) for p in probs)
        self.conflict = ent / math.log(max(2, len(probs)))
        return self.conflict
