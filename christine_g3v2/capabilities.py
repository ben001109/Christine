from __future__ import annotations
import importlib
from typing import Any
from .contracts import Artifact,Intent
class NativeGeneratorAdapter:
    """Only discovers an explicitly Christine-owned hook. No Ollama/open-source model."""
    def __init__(self):
        try:self.generator=importlib.import_module('christine_native_generator')
        except Exception:self.generator=None
    @property
    def ready(self):return self.generator is not None
    def code(self,goal,context):
        if self.generator is None or not hasattr(self.generator,'generate_code'):return None
        try:content=str(self.generator.generate_code(goal,context) or '').strip()
        except Exception:return None
        return Artifact('code',content,language='python' if 'python' in goal.casefold() else '')
    def image(self,goal,context):
        if self.generator is None or not hasattr(self.generator,'generate_image'):return None
        try:path=str(self.generator.generate_image(goal,context) or '').strip()
        except Exception:return None
        return Artifact('image','',path=path)
class Clarifier:
    @staticmethod
    def respond(intent:Intent):
        if 'target_platform' in intent.missing_slots:return '可以做，但「外掛」一定要先知道掛在哪裡。請告訴我目標平台／程式／遊戲，以及你希望外掛完成的具體功能；有這兩項後我才會進入生成。'
        if 'purpose' in intent.missing_slots:return '可以寫，但你還沒告訴我程式實際要完成什麼。請給我一個可驗收的目標，例如「非同步抓十個網址並整理標題」或「掃描資料夾建立索引」。在目標不明確前，我不會再隨機丟 quicksort。'
        if 'subject' in intent.missing_slots:return '可以生成圖片，但你還沒說要畫什麼。給我主體、場景或用途其中至少一項。'
        return '這個任務還缺必要條件；請補充你希望最後得到什麼結果。'
