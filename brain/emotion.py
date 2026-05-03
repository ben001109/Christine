"""
emotion.py — Russell 1980 valence-arousal / Panksepp 7 基本情緒
=================================================================
"""
from __future__ import annotations
class Emotion:
    PANKSEPP = ("SEEKING","RAGE","FEAR","LUST","CARE","PANIC","PLAY")
    def __init__(self):
        self.valence = 0.0   # -1..1
        self.arousal = 0.0   # 0..1
        self.panksepp = {k: 0.0 for k in self.PANKSEPP}
    def update(self, valence=None, arousal=None, panksepp=None, alpha=0.3):
        if valence is not None:
            self.valence = (1-alpha)*self.valence + alpha*float(valence)
        if arousal is not None:
            self.arousal = (1-alpha)*self.arousal + alpha*float(arousal)
        if panksepp:
            for k,v in panksepp.items():
                if k in self.panksepp:
                    self.panksepp[k] = (1-alpha)*self.panksepp[k] + alpha*float(v)
    def banner(self):
        v = self.valence; a = self.arousal
        face = "🙂" if v>0.3 else ("😐" if v>-0.3 else "😟")
        return f"{face} val={v:+.2f} aro={a:.2f}"
