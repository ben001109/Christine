# Christine Model Factory

The Model Factory prepares Christine-specific local models or adapters. It does
not train from scratch and does not bypass runtime safety gates.

Training preconditions:
- legal source approval for every dataset and teacher output.
- Corpus filter and privacy review for any memory-derived examples.
- eval gate passing before runtime use.
- LoRA or QLoRA first; full fine-tuning only after explicit approval.
- do not commit model artifacts, datasets, checkpoints, eval outputs, or weights.
