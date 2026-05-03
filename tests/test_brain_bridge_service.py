class FakeBrain:
    def __init__(self):
        self.enable_mega_calls = []

    def perceive_text(self, text):
        return {"loss": 0.25, "understanding": {"intent": "greet"}, "valence": 0.2}

    def respond(self, seed=None, max_len=80):
        return f"reply:{seed}:{max_len}"

    def dream(self, cycles=3):
        return int(cycles)

    def understand(self, text):
        return {"intent": "statement", "text": text}

    def status(self):
        return {"size": "fake", "ticks": 1}

    def enable_mega(self, active_pool=64, sample_per_tick=8):
        self.enable_mega_calls.append((active_pool, sample_per_tick))
        return True


from christine.brain_bridge.service import BrainService, BrainServiceConfig


def test_brain_service_builds_brain_once():
    calls = []

    def factory(**kwargs):
        calls.append(kwargs)
        return FakeBrain()

    service = BrainService(
        BrainServiceConfig(size="tiny", seed=7, warmup=False, auto_mega=False),
        brain_factory=factory,
    )

    first = service.ensure_brain()
    second = service.ensure_brain()

    assert first is second
    assert calls == [{"size": "tiny", "seed": 7, "warmup": False}]
    assert service.state.ready is True
    assert service.state.err is None
    assert service.state.build_ms is not None


def test_brain_service_say_updates_call_accounting():
    service = BrainService(
        BrainServiceConfig(auto_mega=False),
        brain_factory=lambda **kwargs: FakeBrain(),
    )

    perception, response = service.say("你好", max_len=12)

    assert perception["loss"] == 0.25
    assert response == "reply:你好:12"
    assert service.state.total_calls == 1
    assert service.state.last_loss == 0.25
    assert service.state.last_response == response
    assert service.state.total_perceive_ms >= 0.0


def test_brain_service_returns_unavailable_message_when_factory_fails():
    def broken_factory(**kwargs):
        raise RuntimeError("boom")

    service = BrainService(
        BrainServiceConfig(auto_mega=False),
        brain_factory=broken_factory,
    )

    perception, response = service.say("hello")

    assert perception is None
    assert response.startswith("[brain unavailable: RuntimeError: boom]")
    assert service.state.ready is False
    assert service.state.err == "RuntimeError: boom"


def test_brain_service_auto_enables_mega_when_generated_areas_exist(tmp_path):
    generated = tmp_path / "brain" / "generated"
    generated.mkdir(parents=True)
    (generated / "area_000001.py").write_text("# generated marker\n", encoding="utf-8")

    service = BrainService(
        BrainServiceConfig(auto_mega=True, generated_dir=generated),
        brain_factory=lambda **kwargs: FakeBrain(),
    )

    brain = service.ensure_brain()

    assert brain.enable_mega_calls == [(64, 8)]
    assert service.state.mega_auto is True
    assert service.state.mega_areas_disk == 1
