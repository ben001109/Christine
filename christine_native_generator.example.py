"""Christine-owned generation hook example for G3 v2.0.

Copy/rename this to `christine_native_generator.py` and connect YOUR native
Christine decoder/generator. The unified kernel intentionally does not import
Ollama or a third-party open-source model here.
"""


def generate_code(goal: str, context: dict) -> str:
    raise NotImplementedError("Connect Christine's native code generator here")


def generate_image(goal: str, context: dict) -> str:
    raise NotImplementedError("Return the generated image file path here")
