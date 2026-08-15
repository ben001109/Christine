from __future__ import annotations
import os,time
from .kernel import UnifiedKernel

def main():
    print('='*100);print(' Christine G3 v2.1 — PRISM + ATLAS-138');print(' Intent → Context → 138B/LongDoc/ORBIT → FactGraph → PRISM → Verify → NOVA');print(' Native synthesis path does not require Ollama/open-source LLMs.');print('='*100)
    k=UnifiedKernel();s=k.memory.status();print(f" 5D9A address space: {s['capacity_tokens']:,} tokens");print(f" 5D9A L0 leaves: {s['leaf_count']:,} | local sparse records: {s['loaded_records']}");print(f" NativeGenerator: {'ready' if k.generator.ready else 'not connected'}");print(' Commands: /status, /ingest <path>, /clear, exit\n')
    while True:
        try:raw=input('你：').strip()
        except (EOFError,KeyboardInterrupt):print();break
        if not raw:continue
        if raw.casefold() in {'exit','quit','bye'}:break
        if raw=='/clear':os.system('cls' if os.name=='nt' else 'clear');continue
        if raw=='/status':print(k.memory.status());print(f'documents={len(k.documents.blocks)} native_generator={k.generator.ready}\n');continue
        if raw.startswith('/ingest '):print('Christine：'+k.ingest_file(raw[8:].strip())+'\n');continue
        t=time.perf_counter();answer,turn=k.ask(raw);print('Christine：'+answer);print(f"  [G3 v2.1 trace: {' | '.join(turn.trace)} | {time.perf_counter()-t:.2f}s]\n")
    return 0
if __name__=='__main__':raise SystemExit(main())
