"""
gwt.py — Global Workspace Theory (Baars 1988 / Dehaene 2011)
=============================================================
各模組競爭 limited-capacity workspace；勝者 broadcast 給所有其他模組。
實作：modules 每步 submit (content, salience)；workspace 取 argmax；
broadcast = 把勝者寫進一個 shared blackboard，其他模組讀得到。
"""
from __future__ import annotations
import time


class GlobalWorkspace:
    def __init__(self, capacity=1):
        self.capacity = capacity
        self.blackboard = []   # 最近 N 個 winners
        self.subs = []
        self.history = []

    def submit(self, source, content, salience):
        self.subs.append({"src": source, "content": content,
                          "salience": float(salience), "t": time.time()})

    def cycle(self):
        if not self.subs: return None
        self.subs.sort(key=lambda d: d["salience"], reverse=True)
        winners = self.subs[:self.capacity]
        self.subs = []
        for w in winners:
            self.blackboard.append(w)
            if len(self.blackboard) > 20: self.blackboard.pop(0)
            self.history.append(w)
        return winners[0] if winners else None

    def read(self):
        return self.blackboard[-1] if self.blackboard else None
