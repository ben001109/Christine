from brain import build_default_brain


def test_brain_can_understand_and_respond():
    brain = build_default_brain(size="tiny", warmup=False)

    perception = brain.perceive_text("你好 Christine")

    assert "understanding" in perception
    assert isinstance(brain.respond("你好 Christine"), str)
