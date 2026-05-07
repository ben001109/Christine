from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class DistillationSourceKind(str, Enum):
    PROJECT_CORPUS = "project_corpus"
    PRIVATE_MEMORY = "private_memory"
    TEACHER_OUTPUT = "teacher_output"
    SYNTHETIC_SELF_PLAY = "synthetic_self_play"

    @classmethod
    def _missing_(cls, value):
        raise ValueError(f"unknown distillation source kind: {value}")


@dataclass(frozen=True)
class DistillationDataSource:
    name: str
    kind: DistillationSourceKind
    license: str
    reviewed: bool = False


@dataclass(frozen=True)
class DistillationSourceDecision:
    allowed: bool
    reason: str


APPROVED_TEACHER_LICENSES = {"apache-2.0", "mit", "cc-by-4.0", "project-owned"}


def validate_distillation_source(source: DistillationDataSource) -> DistillationSourceDecision:
    if source.kind == DistillationSourceKind.PRIVATE_MEMORY and not source.reviewed:
        return DistillationSourceDecision(False, "unreviewed-private-source")
    if source.kind == DistillationSourceKind.TEACHER_OUTPUT and source.license not in APPROVED_TEACHER_LICENSES:
        return DistillationSourceDecision(False, "teacher-license-not-approved")
    if not source.reviewed:
        return DistillationSourceDecision(False, "source-not-reviewed")
    return DistillationSourceDecision(True, "allowed")
