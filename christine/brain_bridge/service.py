from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import time
from typing import Any, Callable


BrainFactory = Callable[..., Any]


@dataclass(frozen=True)
class BrainServiceConfig:
    size: str = "small"
    seed: int = 42
    warmup: bool = True
    auto_mega: bool = True
    active_pool: int = 64
    sample_per_tick: int = 8
    generated_dir: Path | None = None


@dataclass
class BrainServiceState:
    ready: bool = False
    err: str | None = None
    build_ms: float | None = None
    total_calls: int = 0
    total_perceive_ms: float = 0.0
    last_loss: Any = None
    last_response: str = ""
    mega_auto: bool = False
    mega_areas_disk: int = 0


def _default_brain_factory(**kwargs: Any) -> Any:
    from brain.brain import build_default_brain

    return build_default_brain(**kwargs)


def _default_generated_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "brain" / "generated"


class BrainService:
    def __init__(
        self,
        config: BrainServiceConfig | None = None,
        brain_factory: BrainFactory | None = None,
    ):
        self.config = config or BrainServiceConfig()
        self.state = BrainServiceState()
        self._brain_factory = brain_factory or _default_brain_factory
        self._brain: Any | None = None

    @property
    def brain(self) -> Any | None:
        return self._brain

    def ensure_brain(self) -> Any | None:
        if self._brain is not None:
            return self._brain
        try:
            t0 = time.time()
            self._brain = self._brain_factory(
                size=self.config.size,
                seed=self.config.seed,
                warmup=self.config.warmup,
            )
            self.state.ready = True
            self.state.err = None
            self.state.build_ms = (time.time() - t0) * 1000.0
            self._auto_enable_mega()
            return self._brain
        except Exception as exc:
            self.state.ready = False
            self.state.err = f"{type(exc).__name__}: {exc}"
            self._brain = None
            return None

    def _auto_enable_mega(self) -> None:
        if not self.config.auto_mega or self._brain is None:
            return
        generated_dir = self.config.generated_dir or _default_generated_dir()
        try:
            areas = [
                path for path in generated_dir.iterdir()
                if path.name.startswith("area_") and path.suffix == ".py"
            ]
        except OSError:
            areas = []
        self.state.mega_areas_disk = len(areas)
        if not areas or not hasattr(self._brain, "enable_mega"):
            self.state.mega_auto = False
            return
        try:
            self.state.mega_auto = bool(
                self._brain.enable_mega(
                    active_pool=self.config.active_pool,
                    sample_per_tick=self.config.sample_per_tick,
                )
            )
        except Exception:
            self.state.mega_auto = False

    def unavailable_message(self) -> str:
        return f"[brain unavailable: {self.state.err}]"

    def say(self, text: str, max_len: int = 48) -> tuple[dict[str, Any] | None, str]:
        brain = self.ensure_brain()
        if brain is None:
            return None, self.unavailable_message()
        t0 = time.time()
        perception = brain.perceive_text(str(text))
        response = brain.respond(seed=str(text), max_len=max_len)
        dt_ms = (time.time() - t0) * 1000.0
        self.state.total_calls += 1
        self.state.total_perceive_ms += dt_ms
        self.state.last_loss = perception.get("loss") if isinstance(perception, dict) else None
        self.state.last_response = response
        return perception, response

    def dream(self, cycles: int = 3) -> int | str:
        brain = self.ensure_brain()
        if brain is None:
            return self.unavailable_message()
        return brain.dream(cycles=int(cycles))

    def understand(self, text: str) -> dict[str, Any] | str:
        brain = self.ensure_brain()
        if brain is None:
            return self.unavailable_message()
        return brain.understand(str(text))

    def status(self) -> dict[str, Any] | str:
        brain = self.brain
        if brain is None:
            return "大腦尚未啟動"
        return brain.status()
