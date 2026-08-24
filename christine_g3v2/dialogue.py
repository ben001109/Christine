from __future__ import annotations
import re
from .utils import clean
class NativeDialogue:
    def respond(self,raw,intent,ctx):
        text=clean(raw);entities=tuple(dict.fromkeys(intent.entities+ctx.inherited_entities))
        if re.search(r'(女朋友|伴侶).{0,20}(性侵|侵害)',text) or re.search(r'(不反抗|不逃|僵住).{0,30}(默認|同意|為什麼)',text):
            return '你抓到了一個很重要的點：人在受到威脅時，不只會「打」或「跑」，也可能直接僵住。這種僵住常常是自動的防衛反應，不是當事人冷靜決定「我不反抗」。所以沒有立刻逃、沒有明顯反抗，不能被當成同意或默認。如果你是在重新理解你女朋友的經歷，比起用事後視角追問她當時為什麼沒做某個動作，更有幫助的是理解她當時可能處在什麼狀態，以及現在她希望得到怎樣的支持。'
        if re.search(r'(真的非常感謝|很感謝|因為他的影片|支撐著現在的我|影響.*現在的我)',text):
            who='、'.join(entities) if entities else '那支影片／那位創作者';return f'聽起來{who}對你不只是「一支看過的影片」，而是幫你重新理解了一段原本很難消化的事情。它可能替你提供了一套語言和框架，讓原本只有困惑、甚至責怪的地方開始變得能理解。如果你之後想向對方表達感謝，把「它具體改變了我怎麼理解這件事」說出來，會比只說謝謝更有力量。'
        if re.search(r'(斗內|donate|可以幫我@|@錫蘭)',text,re.I):
            who='、'.join(entities) if entities else '對方';return f'聽得出來你真的很想讓{who}知道他的內容幫到你。如果你想寫公開留言，我可以幫你整理；至於十萬這種金額很大，不用在情緒最滿的時候立刻決定，先把感謝說清楚就已經很有份量。'
        if ctx.continuity>=.34:return f'我有接住前面的脈絡。你現在是在延續「{ctx.topic}」，我會沿著同一個主題回應。'
        if re.search(r'^(你好|嗨|哈囉|hi|hello)',text,re.I):return '你好，我在。你可以延續前一個主題，也可以直接換一個新問題。'
        return '我有在聽。你直接把現在最想講的內容接下去，我會把這一輪和必要的前文一起理解。'
