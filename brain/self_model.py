"""
self_model.py — Metzinger 2003 / Damasio core-self
====================================================
最小的「我」模型：
  - body schema (homeostasis variables)
  - narrative self (recent episodes)
  - agency (最近一次『我做了什麼』)
"""
from __future__ import annotations
import time

class SelfModel:
    def __init__(self):
        self.body = {"energy": 1.0, "stress": 0.0, "uptime": time.time()}
        self.recent_actions = []
        self.name = "Christine"

    def act_log(self, action, outcome=None):
        self.recent_actions.append({"a": action, "o": outcome, "t": time.time()})
        if len(self.recent_actions) > 200: self.recent_actions.pop(0)

    def update_body(self, d_energy=0.0, d_stress=0.0):
        self.body["energy"] = max(0.0, min(1.0, self.body["energy"] + d_energy))
        self.body["stress"] = max(0.0, min(1.0, self.body["stress"] + d_stress))

    def first_person_report(self):
        uptime = time.time() - self.body["uptime"]
        last = self.recent_actions[-1]["a"] if self.recent_actions else "(剛醒來)"
        return (f"我是 {self.name}；醒著 {uptime:.0f} 秒；"
                f"能量 {self.body['energy']:.2f}；壓力 {self.body['stress']:.2f}；"
                f"上一件事：{last}")
