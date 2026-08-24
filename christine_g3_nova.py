from __future__ import annotations

import ast
import difflib
import hashlib
import json
import os
import re
import time
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

import christine_g3_frontier as g3
import christine_g3_narrative_patch as v13


FIVED9A_TOKEN_CAPACITY = v13.FIVED9A_TOKEN_CAPACITY
NOVA_STATE_PATH = Path(os.environ.get("CHRISTINE_G3_NOVA_STATE", "data/g3_nova_state.json"))
NOVA_MAX_HISTORY = int(os.environ.get("CHRISTINE_G3_NOVA_HISTORY", "96"))
NOVA_MAX_RETRIES = int(os.environ.get("CHRISTINE_G3_NOVA_RETRIES", "3"))


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def _extract_code(text: str) -> str:
    m = re.search(r"```(?:python|py|javascript|js|typescript|ts|java|cpp|c\+\+|c|rust|go)?\s*(.*?)```", text, re.S | re.I)
    if m:
        return m.group(1).strip()
    return str(text or "").strip()


def _semantic_normalize(text: str) -> str:
    s = re.sub(r"\s+", "", str(text or "").casefold())
    replacements = (
        ("一名", "一位"),
        ("大約", "約"),
        ("大概", "約"),
        ("而且", "並"),
        ("並且", "並"),
        ("目前的", "目前"),
        ("資料顯示", "資料指出"),
        ("資訊顯示", "資料指出"),
        ("這個人物", "此人"),
        ("這位人物", "此人"),
        ("是一位", "是"),
        ("是一名", "是"),
        ("具有", "有"),
    )
    for a, b in replacements:
        s = s.replace(a, b)
    return re.sub(r"[，。！？、；：,.!?;:()（）\[\]「」『』\s]", "", s)


def _ngrams(text: str, n: int = 4) -> set[str]:
    s = re.sub(r"\s+", " ", str(text or "").casefold()).strip()
    if len(s) < n:
        return {s} if s else set()
    return {s[i:i+n] for i in range(len(s)-n+1)}


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / max(1, len(a | b))


class _ASTShape(ast.NodeTransformer):
    """Normalize superficial code details before comparing algorithm shape."""

    def visit_Name(self, node: ast.Name):
        return ast.copy_location(ast.Name(id="_V", ctx=node.ctx), node)

    def visit_arg(self, node: ast.arg):
        return ast.copy_location(ast.arg(arg="_A", annotation=None, type_comment=None), node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        node.name = "_F"
        self.generic_visit(node)
        return node

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        node.name = "_AF"
        self.generic_visit(node)
        return node

    def visit_ClassDef(self, node: ast.ClassDef):
        node.name = "_C"
        self.generic_visit(node)
        return node

    def visit_Constant(self, node: ast.Constant):
        if isinstance(node.value, str):
            value = "_S"
        elif isinstance(node.value, (int, float, complex)):
            value = 0
        elif node.value is None:
            value = None
        elif isinstance(node.value, bool):
            value = False
        else:
            value = "_K"
        return ast.copy_location(ast.Constant(value=value), node)


def _python_ast_shape(code: str) -> str:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return ""
    tree = _ASTShape().visit(tree)
    ast.fix_missing_locations(tree)
    return ast.dump(tree, annotate_fields=False, include_attributes=False)


def _fingerprint(text: str, output_kind: str) -> dict[str, str]:
    raw = str(text or "")
    normalized = re.sub(r"\s+", " ", raw.casefold()).strip()
    data = {
        "exact": hashlib.blake2b(normalized.encode("utf-8", "replace"), digest_size=16).hexdigest(),
        "normalized": normalized[:16000],
        "kind": output_kind,
    }
    if output_kind == "code":
        code = _extract_code(raw)
        data["code"] = code[:24000]
        data["ast"] = _python_ast_shape(code)[:32000]
    return data


@dataclass
class NoveltyRecord:
    task_key: str
    user_input: str
    output_kind: str
    answer: str
    exact: str
    normalized: str
    ast_shape: str = ""
    timestamp: float = field(default_factory=time.time)


@dataclass(frozen=True)
class NoveltyVerdict:
    accepted: bool
    duplicate_score: float
    reason: str
    matched_task: str = ""


class NOVAMemory:
    def __init__(self, maxlen: int = NOVA_MAX_HISTORY, state_path: Path | None = NOVA_STATE_PATH):
        self.rows: deque[NoveltyRecord] = deque(maxlen=maxlen)
        self.state_path = state_path
        self._load()

    def add(self, task_key: str, user_input: str, output_kind: str, answer: str) -> None:
        fp = _fingerprint(answer, output_kind)
        self.rows.append(NoveltyRecord(
            task_key=task_key,
            user_input=user_input,
            output_kind=output_kind,
            answer=str(answer or "")[:24000],
            exact=fp["exact"],
            normalized=fp["normalized"],
            ast_shape=fp.get("ast", ""),
        ))
        self._save()

    def recent_for(self, task_key: str, output_kind: str, limit: int = 12) -> list[NoveltyRecord]:
        matches = [
            row for row in reversed(self.rows)
            if row.output_kind == output_kind and (
                row.task_key == task_key
                or self._task_similarity(row.task_key, task_key) >= 0.72
            )
        ]
        return matches[:limit]

    @staticmethod
    def _task_similarity(a: str, b: str) -> float:
        return _jaccard(g3._tokens(a), g3._tokens(b))

    def _save(self) -> None:
        if self.state_path is None:
            return
        try:
            self.state_path.parent.mkdir(parents=True, exist_ok=True)
            payload = [
                {
                    "task_key": r.task_key,
                    "user_input": r.user_input,
                    "output_kind": r.output_kind,
                    "answer": r.answer,
                    "exact": r.exact,
                    "normalized": r.normalized,
                    "ast_shape": r.ast_shape,
                    "timestamp": r.timestamp,
                }
                for r in self.rows
            ]
            tmp = self.state_path.with_suffix(".tmp")
            tmp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            tmp.replace(self.state_path)
        except Exception:
            pass

    def _load(self) -> None:
        if self.state_path is None or not self.state_path.exists():
            return
        try:
            payload = json.loads(self.state_path.read_text(encoding="utf-8"))
            for x in payload[-self.rows.maxlen:]:
                self.rows.append(NoveltyRecord(
                    task_key=str(x.get("task_key", "")),
                    user_input=str(x.get("user_input", "")),
                    output_kind=str(x.get("output_kind", "text")),
                    answer=str(x.get("answer", "")),
                    exact=str(x.get("exact", "")),
                    normalized=str(x.get("normalized", "")),
                    ast_shape=str(x.get("ast_shape", "")),
                    timestamp=float(x.get("timestamp", time.time())),
                ))
        except Exception:
            self.rows.clear()


class NOVAGate:
    def __init__(self, memory: NOVAMemory):
        self.memory = memory

    def evaluate(self, task_key: str, output_kind: str, answer: str) -> NoveltyVerdict:
        fp = _fingerprint(answer, output_kind)
        history = self.memory.recent_for(task_key, output_kind)
        if not history:
            return NoveltyVerdict(True, 0.0, "novel-first-output")

        best = 0.0
        matched = ""
        best_reason = "novel"

        for old in history:
            if fp["exact"] == old.exact:
                score = 1.0
                reason = "exact-repeat"
            elif output_kind == "code":
                score, reason = self._code_similarity(fp, old)
            else:
                score, reason = self._text_similarity(fp["normalized"], old.normalized)

            if score > best:
                best = score
                matched = old.task_key
                best_reason = reason

        threshold = 0.74 if output_kind == "code" else 0.82
        return NoveltyVerdict(
            accepted=best < threshold,
            duplicate_score=best,
            reason=best_reason if best >= threshold else "novel-enough",
            matched_task=matched,
        )

    @staticmethod
    def _text_similarity(a: str, b: str) -> tuple[float, str]:
        na = _semantic_normalize(a)
        nb = _semantic_normalize(b)
        seq = difflib.SequenceMatcher(None, na, nb).ratio()
        tok = _jaccard(g3._tokens(na), g3._tokens(nb))
        bigram = _jaccard(_ngrams(na, 2), _ngrams(nb, 2))
        fourgram = _jaccard(_ngrams(na, 4), _ngrams(nb, 4))
        score = 0.38 * seq + 0.22 * tok + 0.25 * bigram + 0.15 * fourgram
        return score, "semantic-text-repeat"

    @staticmethod
    def _code_similarity(fp: dict[str, str], old: NoveltyRecord) -> tuple[float, str]:
        code = fp.get("code", "")
        old_code = old.answer
        lexical = difflib.SequenceMatcher(None, code, old_code).ratio()
        ast_a = fp.get("ast", "")
        ast_b = old.ast_shape
        structural = difflib.SequenceMatcher(None, ast_a, ast_b).ratio() if ast_a and ast_b else 0.0
        token = _jaccard(g3._tokens(code), g3._tokens(old_code))
        score = 0.52 * structural + 0.28 * token + 0.20 * lexical
        reason = "code-structure-repeat" if structural >= 0.78 else "code-content-repeat"
        return score, reason


class RepeatAwareThread(v13.v12.THREADContext):
    def is_followup(self, text: str) -> bool:
        current = re.sub(r"\s+", " ", str(text or "")).strip().casefold()
        if self.last:
            previous = re.sub(r"\s+", " ", self.last.user_input).strip().casefold()
            if current and current == previous:
                return True
        return super().is_followup(text)


class RuntimeProtocol(Protocol):
    def ask(self, user_input: str) -> tuple[str, g3.TurnEnvelope]: ...


class NOVARuntime:
    """v1.4 anti-repetition wrapper around v1.3."""

    def __init__(self, inner: RuntimeProtocol | None = None, memory: NOVAMemory | None = None,
                 max_retries: int = NOVA_MAX_RETRIES):
        self.inner = inner or v13.ChristineG3NarrativeRuntime(thread=RepeatAwareThread())
        self.novelty_memory = memory or NOVAMemory()
        self.gate = NOVAGate(self.novelty_memory)
        self.max_retries = max(0, max_retries)

    def ask(self, user_input: str) -> tuple[str, g3.TurnEnvelope]:
        answer, turn = self.inner.ask(user_input)
        contract = turn.contract or g3.ContractParser().parse(user_input)
        task_key = self._task_key(contract, user_input)

        verdict = self.gate.evaluate(task_key, contract.output_kind, answer)
        turn.trace.append(f"nova:{verdict.reason}:{verdict.duplicate_score:.2f}")

        if verdict.accepted:
            self.novelty_memory.add(task_key, user_input, contract.output_kind, answer)
            return answer, turn

        candidates: list[tuple[float, str, g3.TurnEnvelope]] = [(verdict.duplicate_score, answer, turn)]

        for attempt in range(1, self.max_retries + 1):
            diversified = self._diversity_request(
                original_goal=contract.goal or user_input,
                original_user_input=user_input,
                output_kind=contract.output_kind,
                attempt=attempt,
                previous=self.novelty_memory.recent_for(task_key, contract.output_kind, limit=5),
            )
            candidate, retry_turn = self._isolated_retry(diversified)
            retry_verdict = self.gate.evaluate(task_key, contract.output_kind, candidate)
            retry_turn.trace.append(f"nova-retry:{attempt}:{retry_verdict.reason}:{retry_verdict.duplicate_score:.2f}")
            candidates.append((retry_verdict.duplicate_score, candidate, retry_turn))

            if retry_verdict.accepted:
                self.novelty_memory.add(task_key, user_input, contract.output_kind, candidate)
                turn.trace.append(f"nova:selected-retry:{attempt}")
                return candidate, turn

        best_score, best_answer, _ = min(candidates, key=lambda x: x[0])
        if best_score < (0.74 if contract.output_kind == "code" else 0.82):
            self.novelty_memory.add(task_key, user_input, contract.output_kind, best_answer)
            turn.trace.append(f"nova:selected-best:{best_score:.2f}")
            return best_answer, turn

        blocked = self._blocked_message(contract.output_kind)
        turn.trace.append("nova:blocked-repeat")
        return blocked, turn

    def _isolated_retry(self, diversified_prompt: str) -> tuple[str, g3.TurnEnvelope]:
        try:
            if isinstance(self.inner, v13.ChristineG3NarrativeRuntime):
                temp_thread = RepeatAwareThread(state_path=None)
                temp = v13.ChristineG3NarrativeRuntime(
                    memory=self.inner.memory,
                    web=self.inner.web,
                    thread=temp_thread,
                    sage=self.inner.sage,
                )
                return temp.ask(diversified_prompt)
        except Exception:
            pass
        return self.inner.ask(diversified_prompt)

    @staticmethod
    def _task_key(contract: g3.TaskContract, raw: str) -> str:
        goal = re.sub(r"\s+", " ", str(contract.goal or raw)).strip().casefold()
        goal = re.sub(r"\[nova[^\]]*\].*$", "", goal, flags=re.I | re.S).strip()
        return f"{contract.operation}|{contract.output_kind}|{goal}"

    @staticmethod
    def _diversity_request(*, original_goal: str, original_user_input: str, output_kind: str,
                           attempt: int, previous: list[NoveltyRecord]) -> str:
        avoid = NOVARuntime._avoidance_features(previous, output_kind)
        if output_kind == "code":
            requirements = (
                "請完成同一個原始程式任務，但這次必須使用實質不同的解法。"
                "至少改變兩項：核心演算法、資料結構、控制流程、函式分解、狀態表示或並行模型。"
                "不得只改變變數名稱、註解、排版或函式名稱。"
            )
        else:
            requirements = (
                "請回答同一個原始問題，但這次必須提供新的資訊組織、不同的切入角度，"
                "不得重複上一版的句型、段落順序或主要內容。"
            )
        return (
            f"{original_goal}\n"
            f"[NOVA diversity attempt {attempt}] {requirements}\n"
            f"上一版應避免重用的特徵：{avoid or '同一內容與同一結構'}。\n"
            "這是內部多樣性約束，不要在最終回答中提到 NOVA、重試或這段指令。"
        )

    @staticmethod
    def _avoidance_features(previous: list[NoveltyRecord], output_kind: str) -> str:
        if not previous:
            return ""
        features: list[str] = []
        for rec in previous[:3]:
            if output_kind == "code":
                code = _extract_code(rec.answer)
                names = re.findall(r"(?:def|class)\s+([A-Za-z_][A-Za-z0-9_]*)", code)
                imports = re.findall(r"^\s*(?:from\s+([A-Za-z0-9_.]+)|import\s+([A-Za-z0-9_.]+))", code, re.M)
                features.extend(names[:4])
                for a, b in imports[:4]:
                    features.append(a or b)
                if "quicksort" in code.casefold():
                    features.append("recursive quicksort")
                if "asyncio" in code.casefold():
                    features.append("same asyncio architecture")
            else:
                words = [w for w in re.findall(r"[\u3400-\u9fff]{2,}|[A-Za-z]{4,}", rec.answer) if len(w) >= 3]
                features.extend(words[:8])
        return "、".join(dict.fromkeys(f for f in features if f))[:500]

    @staticmethod
    def _blocked_message(output_kind: str) -> str:
        if output_kind == "code":
            return (
                "我偵測到這次生成的程式和上一版在演算法／AST 結構上仍高度重複，"
                "所以我阻止它再次貼出來。下一次必須改用不同的核心方法後才會顯示。"
            )
        return (
            "我偵測到這次回答和前面的內容高度重複，所以先不重貼。"
            "我會等到能提供實質的新資訊或新的解釋角度時再輸出。"
        )


def main() -> int:
    print("=" * 92)
    print(" Christine G3 v1.4 — NOVA Anti-Repetition + SAGE-3 + THREAD + ORBIT + 5D9A 138B")
    print(" Cross-turn exact/text/AST repetition is blocked before display.")
    print(f" 5D9A global address space: {FIVED9A_TOKEN_CAPACITY:,} tokens")
    print("=" * 92)
    runtime = NOVARuntime()
    print("Type 'exit' to quit, 'clear' to clear.\n")

    while True:
        try:
            user = input("你：").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not user:
            continue
        if user.casefold() in {"exit", "quit", "bye"}:
            break
        if user.casefold() == "clear":
            os.system("cls" if os.name == "nt" else "clear")
            continue
        started = time.perf_counter()
        answer, turn = runtime.ask(user)
        elapsed = time.perf_counter() - started
        print(f"Christine：{answer}")
        print(f"  [G3 v1.4 trace: {' | '.join(turn.trace)} | {elapsed:.2f}s]\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
