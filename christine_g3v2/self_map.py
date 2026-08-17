from __future__ import annotations
import ast
from dataclasses import dataclass
from pathlib import Path
from .contracts import Evidence
from .utils import clean, jaccard, stable_id, tokens

@dataclass(frozen=True)
class SelfNode:
    kind: str
    name: str
    module: str
    doc: str
    imports: tuple[str, ...]

class SelfMap:
    """Parse Christine's current Python source tree into a lightweight self-model."""
    SELF_TERMS = (
        "christine", "你自己", "你的架構", "你的系統", "你的功能",
        "5d9a", "prism", "atlas", "nova", "orbit", "truth gate",
        "truth-gate", "memory hygiene", "self-map", "unifiedkernel",
        "nativegenerator", "factgraph",
    )

    def __init__(self, package_dir=None):
        self.package_dir = Path(package_dir) if package_dir else Path(__file__).resolve().parent
        self.nodes = []
        self.parse_errors = []
        self.refresh()

    def refresh(self):
        self.nodes.clear()
        self.parse_errors.clear()
        for path in sorted(self.package_dir.glob("*.py")):
            if path.name.startswith("__"):
                continue
            try:
                source = path.read_text(encoding="utf-8")
                tree = ast.parse(source)
            except Exception as exc:
                self.parse_errors.append(f"{path.name}:{type(exc).__name__}")
                continue
            module = path.stem
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.extend(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports.append(node.module)
            imports = tuple(dict.fromkeys(imports))
            self.nodes.append(SelfNode("module", module, module, clean(ast.get_docstring(tree) or ""), imports))
            for node in tree.body:
                if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                    self.nodes.append(SelfNode(
                        "class" if isinstance(node, ast.ClassDef) else "function",
                        node.name,
                        module,
                        clean(ast.get_docstring(node) or ""),
                        imports,
                    ))

    def status(self):
        return {
            "modules": sum(n.kind == "module" for n in self.nodes),
            "classes": sum(n.kind == "class" for n in self.nodes),
            "functions": sum(n.kind == "function" for n in self.nodes),
            "parse_errors": tuple(self.parse_errors),
        }

    def is_self_query(self, query):
        q = clean(query).casefold()
        return any(term in q for term in self.SELF_TERMS)

    def retrieve(self, query, limit=12):
        qt = tokens(query)
        scored = []
        for node in self.nodes:
            text = f"{node.name} {node.module} {node.doc} {' '.join(node.imports)}"
            rel = jaccard(qt, tokens(text))
            if node.name.casefold() in query.casefold() or node.module.casefold() in query.casefold():
                rel = max(rel, .95)
            if rel <= 0:
                continue
            scored.append((
                rel,
                Evidence(
                    stable_id("self-map", node.module, node.kind, node.name),
                    self._sentence(node),
                    f"self-code://christine_g3v2/{node.module}.py",
                    rel,
                    .99,
                    trust=1.0,
                    entity_match=rel,
                    independent_group=f"self-code:{node.module}",
                    origin="self-map",
                ),
            ))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [e for _, e in scored[:limit]]

    def describe(self, query):
        evidence = self.retrieve(query, 10)
        status = self.status()
        q = query.casefold()
        if not evidence and any(x in q for x in ("你自己", "你的架構", "你的系統", "你的功能", "christine")):
            preferred = {"UnifiedKernel", "Memory138", "ResearchEngine", "FactGraph", "PRISMPlanner", "NoveltyGate", "TruthGate", "SelfMap"}
            chosen = [n for n in self.nodes if n.name in preferred][:10]
            evidence = [Evidence(
                stable_id("self-map", n.module, n.kind, n.name),
                self._sentence(n),
                f"self-code://christine_g3v2/{n.module}.py",
                .90,
                .99,
                trust=1.0,
                entity_match=.90,
                independent_group=f"self-code:{n.module}",
                origin="self-map",
            ) for n in chosen]

        if any(x in q for x in ("prism", "atlas", "5d9a", "nova", "orbit", "hygiene", "truth")):
            if not evidence:
                return "我在目前原始碼中沒有找到足夠資訊來可靠描述這個架構模組。", evidence
            return "依照我目前實際載入的原始碼，這個模組可以整理為：" + "；".join(clean(e.content) for e in evidence[:4]) + "。", evidence

        core = self._names(("UnifiedKernel", "Memory138", "ResearchEngine", "FactGraph", "PRISMPlanner", "NoveltyGate", "TruthGate", "SelfMap"))
        answer = (
            "我是 Christine G3 的目前執行核心。我的架構由意圖辨識、上下文、"
            "5D9A 記憶／長文／網路取證、事實圖譜、回答規劃、驗證與防重複等模組協作。"
            f"我剛剛直接掃描目前的 christine_g3v2 原始碼，辨識到 {status['modules']} 個模組、"
            f"{status['classes']} 個 class、{status['functions']} 個頂層 function。"
        )
        if core:
            answer += " 目前可直接確認的核心符號包括：" + "、".join(core) + "。"
        return answer, evidence

    def _names(self, preferred):
        available = {n.name for n in self.nodes}
        return [x for x in preferred if x in available]

    @staticmethod
    def _sentence(node):
        base = f"{node.name} 是 christine_g3v2/{node.module}.py 中的 {node.kind}"
        if node.doc:
            return base + f"，其原始碼說明為：{node.doc[:220]}"
        if node.imports:
            return base + "，此模組直接連結：" + "、".join(node.imports[:8])
        return base + "。"
