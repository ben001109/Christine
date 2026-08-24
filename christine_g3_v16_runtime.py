from __future__ import annotations

import os
import time

import christine_g3_frontier as g3
import christine_g3_v15_runtime as v15r
import christine_g3_v15_intent as v15i
import christine_g3_v16_entity as v16e


FIVED9A_TOKEN_CAPACITY = v15r.FIVED9A_TOKEN_CAPACITY


class ChristineG3V16Runtime(v15r.ChristineG3V15Runtime):
    """
    v1.6: v1.5 intent/context + entity resolution/evidence consensus.

    Entity questions no longer pass through the generic SAGE social-fact parser.
    """

    def __init__(self, *, memory=None, web=None, context=None, nova=None, sage=None,
                 entity_orbit=None, entity_narrative=None):
        super().__init__(
            memory=memory,
            web=web,
            context=context or v16e.ContextGraphV16(),
            nova=nova,
            sage=sage,
        )
        self.intent = v16e.IntentKernelV16()
        self.entity_resolver = v16e.EntityResolver()
        self.entity_orbit = entity_orbit or v16e.EntityORBIT()
        self.entity_narrative = entity_narrative or v16e.EntityNarrative()

    def ask(self, user_input: str) -> tuple[str, g3.TurnEnvelope]:
        raw = v15i._clean(user_input)
        intent = self.intent.analyze(raw)
        resolution = self.context.resolve(raw, intent)

        # Only intercept entity/world-object research; retain v1.5 behavior for
        # support, conversation, clarification, compute and code generation.
        request = self.entity_resolver.from_resolution(resolution)
        if intent.mode in {"inspect_url", "research", "answer"} and request and v16e.is_entity_query(resolution):
            turn = g3.TurnEnvelope(user_input=raw)
            turn.trace.append(f"intent:{intent.mode}")
            turn.trace.append(f"context:{resolution.continuity:.2f}")
            turn.trace.append(f"entity:{request.label or 'url-object'}")
            turn.contract = g3.TaskContract(
                goal=resolution.topic,
                operation="research" if intent.requires_web else "answer",
                output_kind="text",
                requires_facts=True,
                requires_current_info=intent.requires_web,
                requires_web=True,
                success_conditions=("resolve entity before narrating",),
            )

            packet = self.entity_orbit.research(request)
            turn.web_packet = packet
            turn.trace.append(
                f"entity-orbit:{request.source_hint or 'open-web'}:{len(packet.evidence)}:{packet.confidence:.2f}"
            )

            answer, used, meta = self.entity_narrative.synthesize(request, packet)
            turn.trace.append(
                f"entity-facts:{meta.get('facts', 0)} sources={meta.get('sources', 0)}"
            )
            self.context.commit(raw, resolution)
            return answer, turn

        return super().ask(raw)


def main() -> int:
    print("=" * 100)
    print(" Christine G3 v1.6 — Entity Resolution + Evidence Consensus + Context Intent + 5D9A 138B")
    print(" URLs/handles/names are resolved before SAGE narration; low-quality entity noise is rejected.")
    print(f" 5D9A global address space: {FIVED9A_TOKEN_CAPACITY:,} tokens")
    print("=" * 100)
    runtime = ChristineG3V16Runtime()
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
        print(f"  [G3 v1.6 trace: {' | '.join(turn.trace)} | {elapsed:.2f}s]\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
