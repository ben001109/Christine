"""
mega_cortex.py — 把 brain/generated/area_*.py 的 196,896 個 HH MegaCol 接到 Brain
=================================================================================
策略（不可能每 tick 跑 19 萬個 column）：
  1. lazy import — 第一次用到才 import 對應 area
  2. 每 tick 從「啟用集合」隨機抽樣 K 個 area
  3. 每 area 跑一次 biophysical_tick(I, dt)，得 32 個 spike bool
  4. 把所有 spike 摺成一條 length=N_OUT 的 rate 向量
  5. 這條向量被 Brain 加到 cortex hierarchy 的輸入 (additive bias)

論文依據：
  - Mountcastle 1997 「皮質柱是統計樣本，不需全部活化」
  - Buzsáki 2010 「sparse coding：每瞬間只 ~1% 神經元發火」
  - Markram 2015 BBP「整片皮質模擬靠取樣 + 區域聚合」
"""
from __future__ import annotations
import importlib, random, math


class MegaCortex:
    def __init__(self, n_areas_total=6153, active_pool=64, sample_per_tick=8,
                 n_out=32, drive_gain=0.6, seed=0):
        self.N_TOTAL  = n_areas_total
        self.POOL     = active_pool          # 預先 import 的 area 數
        self.K        = sample_per_tick      # 每 tick 跑幾個 area
        self.N_OUT    = n_out
        self.gain     = drive_gain
        self.rng      = random.Random(seed)
        self._areas   = {}                    # idx -> AREA instance
        self._spike_total = 0
        self._tick_count  = 0
        # 預載 active_pool 個 area（前面 + 隨機散布）
        self._preload()

    def _preload(self):
        # 前 POOL/2 個固定載
        head = list(range(1, min(self.POOL // 2 + 1, self.N_TOTAL + 1)))
        # 後 POOL/2 個隨機抽
        rest_n = self.POOL - len(head)
        rest = self.rng.sample(range(len(head)+1, self.N_TOTAL+1),
                                min(rest_n, self.N_TOTAL - len(head)))
        for idx in head + rest:
            self._import_area(idx)

    def _import_area(self, idx):
        if idx in self._areas: return self._areas[idx]
        try:
            mod = importlib.import_module(f"brain.generated.area_{idx:06d}")
            inst = mod.AREA()
            self._areas[idx] = inst
            return inst
        except Exception:
            return None

    def tick(self, drive_vec):
        """
        drive_vec: list[float]  皮質頂層 rep (length 不限)
        回傳: list[float] length=N_OUT，HH spike-rate 摺出來的「神經回響」
        """
        self._tick_count += 1
        if not self._areas: return [0.0] * self.N_OUT

        # 取目前 drive 的能量，當 HH 注入電流（正比例）
        try:
            energy = sum(abs(float(x)) for x in drive_vec) / max(1, len(drive_vec))
        except Exception:
            energy = 0.0
        # 論文：rest=-65mV, V_th=-50mV，Δ=15mV
        # 讓電流在 sub-threshold / supra-threshold 之間擺盪才有豐富 spike pattern
        I = 5.0 + 18.0 * min(1.0, energy * 80.0)   # 5~23 µA/cm²
        dt = 0.5

        # 抽樣 K 個 area
        keys = list(self._areas.keys())
        chosen = self.rng.sample(keys, min(self.K, len(keys)))

        # 摺出 N_OUT 維 spike rate
        out = [0.0] * self.N_OUT
        n_total_cols = 0
        for idx in chosen:
            area = self._areas[idx]
            try:
                spikes = area.biophysical_tick(I=I, dt=dt)
            except Exception:
                continue
            for j, s in enumerate(spikes):
                out[j % self.N_OUT] += 1.0 if s else 0.0
                n_total_cols += 1
                if s: self._spike_total += 1

        # 正規化成 rate (0~1)
        if n_total_cols > 0:
            scale = 1.0 / max(1.0, math.sqrt(n_total_cols))
            out = [v * scale for v in out]
        return out

    def expand(self, n_more):
        """動態多載 n_more 個 area 進 active pool（讓系統「長大」）。"""
        loaded = set(self._areas.keys())
        candidates = [i for i in range(1, self.N_TOTAL+1) if i not in loaded]
        if not candidates: return 0
        pick = self.rng.sample(candidates, min(n_more, len(candidates)))
        added = 0
        for idx in pick:
            if self._import_area(idx) is not None: added += 1
        return added

    def status(self):
        return {
            "n_areas_total": self.N_TOTAL,
            "n_areas_loaded": len(self._areas),
            "sample_per_tick": self.K,
            "n_out": self.N_OUT,
            "spikes_total": self._spike_total,
            "ticks": self._tick_count,
            "rate_avg": self._spike_total / max(1, self._tick_count * self.K * 32),
        }
