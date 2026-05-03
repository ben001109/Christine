"""
Christine Brain —— AGI 腦神經網路（獨立套件）
================================================

寫在 f:\\christine\\brain\\ 下，跟 christine_final.py 解耦。
不灌知識，只靠「結構 + 動力學 + 學習律」從語言輸入自己長出理解。

架構對應的論文（每一支 .py 開頭都有完整引用）：

  neuron.py        Hodgkin-Huxley 1952 / Izhikevich 2003 / LIF
  synapse.py       Hebb 1949 / STDP Bi-Poo 1998 / Oja 1982
  column.py        Mountcastle 1978 cortical column / Hawkins HTM
  region.py        Felleman-Van Essen 1991 hierarchy / Mesulam 1998
  thalamus.py      Sherman-Guillery 2006 thalamo-cortical loop
  hippocampus.py   O'Keefe place cells / Buzsáki sharp-wave ripples
  basal_ganglia.py Doya 1999 / Houk-Adams-Barto 1995 actor-critic
  cerebellum.py    Marr 1969 / Albus 1971 / Ito LTD
  amygdala.py      LeDoux 1996 fear conditioning
  default_mode.py  Raichle 2001 DMN / Andrews-Hanna 2010
  predictive.py    Rao-Ballard 1999 / Friston FEP / Clark 2013
  gwt.py           Baars 1988 / Dehaene 2011 GNW
  iit.py           Tononi 2004 Φ（結構指標，不宣稱意識）
  free_energy.py   Friston 2010
  attention.py     Posner 1980 / Corbetta-Shulman 2002
  embodiment.py    Barsalou 1999 grounded cognition / Lakoff-Johnson
  language.py      Elman 1990 SRN / Chomsky merge / construction grammar
  semantics.py     distributional + grounding（不用預訓練權重）
  emotion.py       Russell 1980 valence-arousal / Panksepp 7 systems
  memory.py        Atkinson-Shiffrin / Tulving episodic/semantic
  dreaming.py      Crick-Mitchison 1983 reverse learning / replay
  self_model.py    Metzinger 2003 / Damasio core self
  theory_of_mind.py Baron-Cohen / Premack-Woodruff 1978
  executive.py     Miller-Cohen 2001 PFC / Norman-Shallice SAS
  homeostasis.py   Cannon 1929 / Sterling allostasis
  oscillator.py    Buzsáki rhythms / Kuramoto coupling
  world_model.py   Ha-Schmidhuber 2018 / Friston active inference
  brain.py         主 orchestrator（把所有子系統連起來）
  generator.py     展開器：把微結構展開成 500k 行磁碟程式

依賴：只用 stdlib + numpy（如有；沒有就 fallback 純 python）。
"""

__version__ = "0.1.0"
__brain_paper_count__ = 27

from .brain import Brain, build_default_brain  # noqa: E402,F401
