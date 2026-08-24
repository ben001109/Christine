from __future__ import annotations
import re
from dataclasses import dataclass
from .contracts import Evidence, Fact
from .utils import clean, jaccard, tokens

@dataclass(frozen=True)
class TruthReport:
    accepted: bool
    grounding_ratio: float
    supported_claims: int
    factual_claims: int
    independent_sources: int
    certainty_violation: bool
    reason: str

class TruthGate:
    """Claim-level grounding gate: certainty may not exceed evidence support."""
    CERTAINTY = re.compile(r"(已驗證|嚴謹無誤|完全確定|可確認為|證實|已證明|毫無疑問|一定是|必然是)", re.I)
    UNCERTAINTY = re.compile(r"(可能|目前|暫時|不確定|不足|尚無|還不能|推測|線索|依目前資料)", re.I)
    META = re.compile(r"(我會|我不能|我目前|這一輪|證據|來源|資料|查到|沒有足夠)", re.I)

    def evaluate(self, answer, *, evidence=(), facts=(), verifier_backed=False):
        answer = clean(answer)
        claims = self._claims(answer)
        sources = {s for f in facts for s in f.sources if s} | {
            e.independent_group or e.source for e in evidence if e.source
        }
        if not claims:
            return TruthReport(True, 1.0, 0, 0, len(sources), False, "no-factual-claims")
        corpus = [f"{f.subject} {f.predicate} {f.value}" for f in facts] + [e.content for e in evidence]
        supported = sum(
            1 for c in claims
            if self._supported(c, corpus) or (verifier_backed and self._looks_derived(c))
        )
        ratio = supported / max(1, len(claims))
        certainty = bool(self.CERTAINTY.search(answer))
        violation = certainty and (ratio < .90 or (not verifier_backed and len(sources) < 2))
        accepted = ratio >= .60 and not violation
        if not evidence and not facts and not verifier_backed:
            accepted = False
            reason = "zero-grounding"
        elif violation:
            reason = "unsupported-certainty"
        elif ratio < .60:
            reason = "low-grounding"
        else:
            reason = "grounded"
        return TruthReport(accepted, ratio, supported, len(claims), len(sources), violation, reason)

    def safe_fallback(self, subject, report):
        if report.reason == "zero-grounding":
            return f"我目前沒有足夠可驗證的資料支持對「{subject}」下確定結論。我可以先從自己的架構、記憶或外部來源取得證據後再回答。"
        if report.reason == "unsupported-certainty":
            return f"目前證據不足以用「已驗證」或「完全確定」的語氣描述「{subject}」。我會保留不確定性，直到有足夠獨立證據或可重現的驗證結果。"
        return (
            f"我取得了一些與「{subject}」相關的資訊，但目前只有 "
            f"{report.supported_claims}/{report.factual_claims} 個主要陳述得到足夠支持；"
            "為避免把推測說成事實，我先不輸出剩餘內容。"
        )

    @classmethod
    def _claims(cls, answer):
        rows = [clean(x) for x in re.split(r"(?<=[。！？.!?])\s+|\n+", answer) if clean(x)]
        out = []
        for row in rows:
            if cls.META.search(row) and cls.UNCERTAINTY.search(row):
                continue
            if re.match(r"^(來源|主要來源|這次主要交叉參考|證據品質|目前證據|trace|G3)", row, re.I):
                continue
            if len(tokens(row)) >= 1 and len(row) >= 8:
                out.append(row)
        return out

    @staticmethod
    def _supported(claim, corpus):
        ct = tokens(claim)
        if not ct:
            return True
        return max((jaccard(ct, tokens(x)) for x in corpus if x), default=0.0) >= .18

    @staticmethod
    def _looks_derived(claim):
        return bool(re.search(r"(因此|所以|可得|推出|等於|結果為|解為|證明)", claim))
