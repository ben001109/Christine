from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class ModelProviderRequest:
    prompt: str
    system: str = ""
    metadata: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ModelProviderResponse:
    available: bool
    text: str
    reason: str = ""


class ModelProvider(Protocol):
    def generate(self, request: ModelProviderRequest) -> ModelProviderResponse: ...


@dataclass(frozen=True)
class NoopModelProvider:
    reason: str = "model provider not configured"

    def generate(self, request: ModelProviderRequest) -> ModelProviderResponse:
        return ModelProviderResponse(False, "", self.reason)
