"""
memory.py — Atkinson-Shiffrin 多儲存 + Tulving episodic/semantic
================================================================
"""
from __future__ import annotations
import time

class Memory:
    def __init__(self, stm_capacity=7, ltm_decay=0.001):
        self.stm = []       # (content, strength, t)
        self.ltm = {}       # key -> (content, strength)
        self.episodes = []  # (timestamp, content)
        self.stm_cap = stm_capacity
        self.decay = ltm_decay

    def perceive(self, content, strength=1.0):
        self.stm.append([content, float(strength), time.time()])
        if len(self.stm) > self.stm_cap:
            old = self.stm.pop(0)
            # 強的自動轉 LTM
            if old[1] > 0.5:
                self._commit_ltm(old[0], old[1])

    def rehearse(self, idx, boost=0.3):
        if 0 <= idx < len(self.stm):
            self.stm[idx][1] += boost

    def _commit_ltm(self, content, strength):
        key = str(content)[:120]
        if key in self.ltm:
            self.ltm[key][1] = min(5.0, self.ltm[key][1] + 0.5)
        else:
            self.ltm[key] = [content, strength]

    def episodic_store(self, content):
        self.episodes.append((time.time(), content))
        if len(self.episodes) > 1000: self.episodes.pop(0)

    def search_ltm(self, key_substr, k=5):
        hits = [(k2, v) for k2,v in self.ltm.items() if key_substr in k2]
        hits.sort(key=lambda x: x[1][1], reverse=True)
        return hits[:k]

    def tick(self):
        """衰減 + 強化。"""
        for k,v in list(self.ltm.items()):
            v[1] -= self.decay
            if v[1] <= 0: del self.ltm[k]
