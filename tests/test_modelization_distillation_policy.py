import pytest

from christine.modelization import (
    DistillationDataSource,
    DistillationSourceKind,
    validate_distillation_source,
)


def test_distillation_policy_accepts_reviewed_project_corpus_source():
    source = DistillationDataSource(
        name="repository-contracts",
        kind=DistillationSourceKind.PROJECT_CORPUS,
        license="project-owned",
        reviewed=True,
    )

    assert validate_distillation_source(source).allowed is True


def test_distillation_policy_rejects_unreviewed_private_memory():
    source = DistillationDataSource(
        name="raw-memory",
        kind=DistillationSourceKind.PRIVATE_MEMORY,
        license="user-private",
        reviewed=False,
    )

    decision = validate_distillation_source(source)

    assert decision.allowed is False
    assert decision.reason == "unreviewed-private-source"


def test_distillation_policy_rejects_unknown_teacher_terms():
    source = DistillationDataSource(
        name="teacher-output",
        kind=DistillationSourceKind.TEACHER_OUTPUT,
        license="unknown",
        reviewed=True,
    )

    decision = validate_distillation_source(source)

    assert decision.allowed is False
    assert decision.reason == "teacher-license-not-approved"


def test_distillation_policy_rejects_unknown_source_kind():
    with pytest.raises(ValueError, match="unknown distillation source kind"):
        DistillationSourceKind("unknown")
