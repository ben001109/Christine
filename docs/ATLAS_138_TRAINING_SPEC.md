# ATLAS-138 — 5D9A 138B Training Specification

ATLAS-138 trains Christine's **virtual 138B-token global memory space**. It does not claim that 138B unseen raw tokens can be gradient-trained instantly or placed in one prompt.

## Address space

- capacity: `138,000,000,000` tokens
- target leaf: `1024` tokens
- L0 capacity: `134,765,625` leaves
- hierarchy fanout: `64`
- about `129` shards at `1,048,576` leaves/shard if the entire capacity were occupied

## Data pipeline

`raw -> provenance -> normalize -> document dedupe -> paragraph-aware leaves -> leaf dedupe -> WCode -> 5D features -> shards -> index snapshot`

WCode is an immutable content identity. Embeddings/coordinates may be rebuilt without changing WCode.

## Five dimensions

### D1 Semantic
Train Christine's own native encoder/reranker using question↔gold-evidence pairs, paraphrases and same-entity independent sources as positives. Use hard negatives such as same-name/wrong-person, lexically similar but unrelated material, and stale facts.

InfoNCE-style objective:

`L_S = -log exp(sim(q,p)/tau) / (exp(sim(q,p)/tau) + sum exp(sim(q,n_i)/tau))`

### D2 Temporal
Use query-conditioned pairwise ranking:

`L_T = -log sigmoid(score(q,new)-score(q,old))`

when freshness matters. Historical queries must still retrieve old evidence; never use one global recency penalty.

### D3 Relational
Train a graph over Entity, Event, Claim, Rule, Procedure, Artifact and Goal nodes. Example edges: `is_a`, `caused_by`, `before`, `after`, `supports`, `contradicts`, `held_role`, `requires`, `derived_from`. Train link prediction against hard non-edges.

### D4 Personal
Personal relevance is a separate utility model. It must never modify factual truth confidence. Learn from explicit feedback, revisits, task success, project recency and save/pin actions. A simple contextual-bandit update is:

`U_(t+1) = U_t + eta * (reward-U_t)`

### D5 Epistemic
Each source keeps a Beta posterior:

`P(correct|source)=alpha/(alpha+beta)`

Verified claim -> `alpha += 1`; correction/false claim -> `beta += 1`. Calibrate final confidence on held-out facts with Brier/log loss. Multiple pages from one domain are not independent sources.

## Joint objective

A recommended starting point for Christine's native 5D encoder/reranker is:

`L_total = 1.00 L_sem + 0.35 L_temp + 0.65 L_rel + 0.25 L_personal + 0.80 L_epi + 1.00 L_rank + 0.50 L_cal`

These are starting hyperparameters, not universal constants; tune them on held-out retrieval and answer-support tasks.

## Retrieval-policy training

Candidate pool:

`SemanticANN ∪ Lexical ∪ EntityGraph ∪ HotVerified`

Rerank using:

`J = relevance + lambda*coverage + mu*epistemic - alpha*redundancy - beta*latency - gamma*stale_conflict`

Curriculum:
1. exact retrieval
2. paraphrase
3. same-name entity disambiguation
4. current-vs-old fact
5. multi-hop relation
6. contradiction
7. multilingual query
8. long-document distributed evidence

## Active context

138B is global memory, not active context. Use:

`hierarchy -> candidate union -> rerank -> graph expansion -> contradiction groups -> MMR -> token-budget selection`

Typical active evidence budget: 8K–16K tokens.

## Crystallization

Do not store only the final prose answer. Store verified abstract facts with subject, predicate, object/value, time/validity interval, source IDs, confidence, version and contradiction links.

## Continual learning

`ORBIT -> evidence verification -> FactGraph -> ATLAS hot_verified`

New verified facts become queryable immediately. Background consolidation later performs dedupe, alias/entity merge, contradiction versioning, source-calibration update, ANN/PQ rebuild, graph compaction and immutable snapshot creation.

## Anti-forgetting

If native encoder/reranker weights change, replay rare entities, old facts, same-name cases, contradictions, Chinese/English mixed queries, social URLs, code/docs queries and previously failed hard examples. Block promotion if the old held-out suite drops by more than 2 percentage points.

## Evaluation gate

Minimum held-out metrics:
- Recall@20 / MRR / nDCG
- same-name entity confusion
- temporal update accuracy
- contradiction resolution
- multi-hop retrieval
- long-document retrieval
- provenance accuracy
- Brier/ECE confidence calibration
- unsupported-memory answer rate
- p50/p95 retrieval latency

Suggested promotion targets:
- Recall@20 >= 0.95
- same-name entity confusion <= 1%
- provenance attached = 100%
- unsupported-memory answer rate <= 1%
- old-suite regression <= 2 percentage points

## Instant startup vs raw training

**Attach** opens an already-built snapshot/index and can be fast. **Raw ingestion/training** must read the data and is physically bounded by I/O and compute. The intended production strategy is bulk ATLAS training offline + fast snapshot attach + immediate online hot-memory assimilation + periodic background consolidation.
