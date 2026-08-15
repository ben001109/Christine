from __future__ import annotations

import hashlib
import json
import math
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Iterator, Protocol, Sequence

from .contracts import TOKEN_CAPACITY_5D9A
from .utils import clamp01, hierarchy_counts, stable_id, tokens


@dataclass(frozen=True)
class RawRecord:
    text: str
    source: str
    timestamp: float | None = None
    namespace: str = "world"
    user_relevance: float = 0.0
    source_trust: float = 0.5


@dataclass(frozen=True)
class TrainingLeaf:
    wcode: str
    text: str
    token_estimate: int
    source: str
    namespace: str
    timestamp: float | None
    semantic_key: tuple[float, ...]
    lexical_terms: tuple[str, ...]
    relation_ids: tuple[str, ...]
    personal_score: float
    epistemic_score: float
    verified: bool


@dataclass(frozen=True)
class TrainingStats:
    records_seen: int
    leaves_written: int
    tokens_estimated: int
    duplicates_removed: int
    verified_leaves: int
    elapsed_seconds: float
    snapshot_path: str


@dataclass(frozen=True)
class Coordinate5D:
    semantic: float
    temporal: float
    relational: float
    personal: float
    epistemic: float


@dataclass
class SourceCalibration:
    alpha: float = 2.0
    beta: float = 2.0

    @property
    def mean(self) -> float:
        return self.alpha / (self.alpha + self.beta)

    def update(self, correct: bool) -> None:
        if correct:
            self.alpha += 1.0
        else:
            self.beta += 1.0


class NativeEncoder(Protocol):
    def encode(self, text: str) -> Sequence[float]: ...


class LexicalProjectionEncoder:
    """Deterministic bootstrapping projection, not a learned semantic model."""

    def __init__(self, dims: int = 256):
        self.dims = dims

    def encode(self, text: str) -> Sequence[float]:
        vec = [0.0] * self.dims
        for term in tokens(text):
            h = int(hashlib.blake2b(term.encode("utf-8", "replace"), digest_size=8).hexdigest(), 16)
            vec[h % self.dims] += 1.0 if ((h >> 8) & 1) else -1.0
        norm = math.sqrt(sum(v*v for v in vec)) or 1.0
        return [v/norm for v in vec]


class ATLAS138Trainer:
    """Adaptive Training & Lifelong Assimilation System for virtual 5D9A 138B.

    This is a memory assimilation/index training system. It explicitly does not
    claim that 138B previously unseen raw tokens can be gradient-trained in zero time.
    """

    def __init__(self, root: str | Path = "data/5d9a_138b", *, encoder: NativeEncoder | None = None,
                 leaf_chars: int = 3600, shard_leaf_limit: int = 1_048_576):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.encoder = encoder or LexicalProjectionEncoder()
        self.leaf_chars = leaf_chars
        self.shard_leaf_limit = shard_leaf_limit
        self.calibration: dict[str, SourceCalibration] = {}
        self._seen_hashes: set[str] = set()

    def train_stream(self, records: Iterable[RawRecord], *, snapshot_name: str | None = None) -> TrainingStats:
        started = time.monotonic()
        snapshot_name = snapshot_name or time.strftime("snapshot-%Y%m%d-%H%M%S")
        snapshot = self.root / snapshot_name
        tmp = self.root / (snapshot_name + ".tmp")
        if tmp.exists():
            import shutil
            shutil.rmtree(tmp)
        (tmp / "shards").mkdir(parents=True)

        records_seen = leaves_written = token_total = duplicates = verified = 0
        shard_index = 0
        shard_count = 0
        fh = self._open_shard(tmp / "shards", shard_index)
        try:
            for raw in records:
                records_seen += 1
                normalized = self._normalize(raw.text)
                if not normalized:
                    continue
                doc_hash = hashlib.blake2b(normalized.encode("utf-8","replace"), digest_size=16).hexdigest()
                if doc_hash in self._seen_hashes:
                    duplicates += 1
                    continue
                self._seen_hashes.add(doc_hash)

                for leaf_text in self._segment(normalized):
                    leaf_hash = hashlib.blake2b(leaf_text.encode("utf-8","replace"), digest_size=16).hexdigest()
                    if leaf_hash in self._seen_hashes:
                        duplicates += 1
                        continue
                    self._seen_hashes.add(leaf_hash)
                    leaf = self._make_leaf(raw, leaf_text)
                    fh.write(json.dumps(asdict(leaf), ensure_ascii=False) + "\n")
                    leaves_written += 1
                    shard_count += 1
                    token_total += leaf.token_estimate
                    verified += int(leaf.verified)
                    if shard_count >= self.shard_leaf_limit:
                        fh.close()
                        shard_index += 1
                        shard_count = 0
                        fh = self._open_shard(tmp / "shards", shard_index)
        finally:
            try:
                fh.close()
            except Exception:
                pass

        manifest = {
            "format": "christine-5d9a-138b-v1",
            "capacity_tokens": TOKEN_CAPACITY_5D9A,
            "leaf_tokens_target": 1024,
            "hierarchy": hierarchy_counts(TOKEN_CAPACITY_5D9A),
            "created_at": time.time(),
            "encoder": type(self.encoder).__name__,
            "records_seen": records_seen,
            "leaves_written": leaves_written,
            "tokens_estimated": token_total,
            "duplicates_removed": duplicates,
            "verified_leaves": verified,
            "shard_count": shard_index + (1 if shard_count else 0),
            "source_calibration": {k: {"alpha": v.alpha, "beta": v.beta, "mean": v.mean} for k, v in self.calibration.items()},
            "training_objectives": self.training_objectives(),
        }
        (tmp / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        if snapshot.exists():
            import shutil
            shutil.rmtree(snapshot)
        tmp.replace(snapshot)
        return TrainingStats(records_seen, leaves_written, token_total, duplicates, verified,
                             time.monotonic()-started, str(snapshot))

    def online_assimilate(self, record: RawRecord, verified: bool) -> TrainingLeaf | None:
        text = self._normalize(record.text)
        if not text:
            return None
        key = hashlib.blake2b(text.encode("utf-8","replace"), digest_size=16).hexdigest()
        if key in self._seen_hashes:
            return None
        self._seen_hashes.add(key)
        if verified:
            self._calibrator(record.source).update(True)
        leaf = self._make_leaf(record, text, force_verified=verified)
        hot = self.root / "hot_verified.jsonl"
        with hot.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(asdict(leaf), ensure_ascii=False) + "\n")
        return leaf

    @staticmethod
    def training_objectives() -> dict[str, str]:
        return {
            "semantic": "Contrastive/listwise ranking over question-evidence, paraphrases and hard entity negatives.",
            "temporal": "Query-conditioned pairwise freshness/order loss; historical queries must not globally punish old evidence.",
            "relational": "Entity/event/claim/procedure graph link prediction with observed edges versus sampled non-edges.",
            "personal": "Separate contextual-bandit utility from user feedback; personal relevance must never alter factual truth confidence.",
            "epistemic": "Source/provenance confidence calibration with Beta posteriors plus held-out Brier/log loss.",
            "retrieval_policy": "Pairwise/listwise reranking reward for supporting evidence, coverage and provenance minus redundancy/latency.",
            "consolidation": "Verified claims crystallize to versioned fact nodes; contradictions remain linked history rather than being deleted.",
        }

    @staticmethod
    def five_d_score(coord: Coordinate5D, *, weights: tuple[float,float,float,float,float]) -> float:
        values = (coord.semantic, coord.temporal, coord.relational, coord.personal, coord.epistemic)
        total = sum(weights) or 1.0
        return sum(w*v for w, v in zip(weights, values)) / total

    def _make_leaf(self, raw: RawRecord, text: str, force_verified: bool | None = None) -> TrainingLeaf:
        source_score = self._source_score(raw.source, raw.source_trust)
        verified = source_score >= .82 if force_verified is None else bool(force_verified)
        return TrainingLeaf(
            wcode=stable_id(raw.namespace, raw.source, text), text=text,
            token_estimate=max(1, len(text)//3), source=raw.source,
            namespace=raw.namespace, timestamp=raw.timestamp,
            semantic_key=tuple(round(float(x), 7) for x in self.encoder.encode(text)),
            lexical_terms=tuple(sorted(tokens(text))[:160]),
            relation_ids=tuple(self._relation_ids(text)),
            personal_score=clamp01(raw.user_relevance), epistemic_score=source_score,
            verified=verified,
        )

    def _source_score(self, source: str, prior: float) -> float:
        return clamp01(.55*clamp01(prior) + .45*self._calibrator(source).mean)

    def _calibrator(self, source: str) -> SourceCalibration:
        return self.calibration.setdefault(source, SourceCalibration())

    @staticmethod
    def _normalize(text: str) -> str:
        return " ".join(str(text or "").replace("\x00", " ").replace("\ufffd", " ").split()).strip()

    def _segment(self, text: str) -> Iterator[str]:
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        if len(paragraphs) <= 1:
            paragraphs = [text[i:i+self.leaf_chars] for i in range(0, len(text), self.leaf_chars)]
        buf: list[str] = []
        size = 0
        for p in paragraphs:
            if buf and size + len(p) > self.leaf_chars:
                yield " ".join(buf)
                buf, size = [], 0
            buf.append(p); size += len(p)
        if buf:
            yield " ".join(buf)

    @staticmethod
    def _relation_ids(text: str) -> list[str]:
        import re
        entities = re.findall(r"[\u3400-\u9fff]{2,8}|[A-Z][A-Za-z0-9_.-]{2,}", text)
        unique = list(dict.fromkeys(entities))[:24]
        out = []
        for i, a in enumerate(unique):
            for b in unique[i+1:i+4]:
                out.append(stable_id("rel", a, b))
        return out[:48]

    @staticmethod
    def _open_shard(shard_dir: Path, index: int):
        return (shard_dir / f"shard-{index:05d}.jsonl").open("w", encoding="utf-8")


def jsonl_records(path: str | Path) -> Iterator[RawRecord]:
    path = Path(path)
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            obj = json.loads(line)
            yield RawRecord(text=str(obj.get("text") or obj.get("content") or ""),
                            source=str(obj.get("source") or path.name),
                            timestamp=obj.get("timestamp"), namespace=str(obj.get("namespace") or "world"),
                            user_relevance=float(obj.get("user_relevance", 0.0) or 0.0),
                            source_trust=float(obj.get("source_trust", 0.5) or 0.5))
