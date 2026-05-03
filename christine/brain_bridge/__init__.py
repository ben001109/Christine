"""Bridge from Christine runtime code to the legacy brain package."""

from .service import BrainService, BrainServiceConfig, BrainServiceState

__all__ = ["BrainService", "BrainServiceConfig", "BrainServiceState"]
