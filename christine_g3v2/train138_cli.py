from __future__ import annotations

import argparse
import json

from .atlas138 import ATLAS138Trainer, jsonl_records


def main() -> int:
    parser = argparse.ArgumentParser(description="Christine ATLAS-138 trainer")
    parser.add_argument("dataset", help="JSONL dataset: text/content + source")
    parser.add_argument("--root", default="data/5d9a_138b")
    parser.add_argument("--snapshot", default=None)
    parser.add_argument("--show-objectives", action="store_true")
    args = parser.parse_args()

    trainer = ATLAS138Trainer(args.root)
    if args.show_objectives:
        print(json.dumps(trainer.training_objectives(), ensure_ascii=False, indent=2))
    stats = trainer.train_stream(jsonl_records(args.dataset), snapshot_name=args.snapshot)
    print(json.dumps(stats.__dict__, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
