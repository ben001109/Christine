from __future__ import annotations
import os,time,json
from .kernel import UnifiedKernel

def main():
    print('='*100)
    print(' Christine G3 v2.4 — 5D9A-OMEGA Cognitive Field Engine')
    print(' 5D9A-OMEGA: Acquire → Abstract → Assess → Access → Assemble → Architect → Act → Audit → Adapt')
    print(' No v1.x wrapper chain. No Ollama/open-source LLM in native synthesis path.')
    print('='*100)
    k=UnifiedKernel();s=k.memory.status()
    print(f" 5D9A virtual capacity: {s['capacity_tokens']:,} tokens")
    print(f" 5D9A confirmed indexed: {s['indexed_tokens']:,} tokens | coverage={s['address_coverage']*100:.6f}%")
    print(f" 5D9A resident sparse: {s['loaded_records']} records / ~{s['resident_sparse_tokens_estimate']:,} tokens")
    print(f" NativeGenerator: {'ready' if k.generator.ready else 'not connected'}")
    sm=k.self_map.status();print(f" SELF-MAP: {sm['modules']} modules / {sm['classes']} classes / {sm['functions']} functions")
    om=k.omega.status();print(f" OMEGA: {om['name']} / {len(om['cycle'])}A / {len(om['dimensions'])}D")
    print(' Commands: /status, /selfmap, /omega, /ingest <path>, /clear, exit\n')
    while True:
        try:raw=input('你：').strip()
        except (EOFError,KeyboardInterrupt):print();break
        if not raw:continue
        if raw.casefold() in {'exit','quit','bye'}:break
        if raw=='/clear':os.system('cls' if os.name=='nt' else 'clear');continue
        if raw=='/status':
            print(json.dumps(k.memory.status(),ensure_ascii=False,indent=2));print(f'documents={len(k.documents.blocks)} native_generator={k.generator.ready}\n');continue
        if raw=='/selfmap':print(json.dumps(k.self_map.status(),ensure_ascii=False,indent=2)+'\n');continue
        if raw=='/omega':print(json.dumps(k.omega.status(),ensure_ascii=False,indent=2)+'\n');continue
        if raw.startswith('/ingest '):print('Christine：'+k.ingest_file(raw[8:].strip())+'\n');continue
        t=time.perf_counter();answer,turn=k.ask(raw);print('Christine：'+answer);print(f"  [G3 v2.4 trace: {' | '.join(turn.trace)} | {time.perf_counter()-t:.2f}s]\n")
    return 0
if __name__=='__main__':raise SystemExit(main())
