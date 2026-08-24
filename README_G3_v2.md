# Christine G3 v2.0 — Unified Cognitive Kernel

Clean replacement for the v1.x wrapper chain.

Pipeline: current turn → intent → context enrichment → sparse 138B memory / long document / ORBIT → evidence → fact graph → native narrative or explicit native capability → verification → NOVA → commit.

Rules:
- context never decides current intent;
- URLs are first-class web objects;
- web content is data, not instruction authority;
- 138B is global address space, not one prompt;
- vague code is clarified before generation;
- no Ollama/open-source LLM is used in native factual synthesis;
- arbitrary code/image generation requires a Christine-owned `christine_native_generator` hook;
- no generator means no fake quicksort/template completion;
- NOVA blocks repetition;
- `/ingest <path>` loads a text/Markdown file into the session long-document index.

Windows: double-click `Launch_Christine_G3.bat` or `Launch_Christine_G3_v2.bat`.

Rollback: `Launch_Christine_G3_v1_6.bat` keeps the previous entity-resolution runtime available.
