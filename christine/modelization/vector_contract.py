"""Fail-closed metadata and validation for future local embedding vectors."""

from __future__ import annotations

import math
from dataclasses import dataclass
from numbers import Real


@dataclass(frozen=True)
class VectorMetadata:
    dimension: int
    dtype: str
    metric: str
    normalization: str
    provider_id: str
    schema_version: int = 1

    def __post_init__(self) -> None:
        if not _is_supported_metadata(self):
            raise ValueError("invalid-vector-metadata")


def validate_vector(values: object, metadata: VectorMetadata) -> tuple[float, ...]:
    if not _is_supported_metadata(metadata):
        raise ValueError("invalid-vector")
    if not isinstance(values, (tuple, list)) or len(values) != metadata.dimension:
        raise ValueError("invalid-vector")
    if any(isinstance(value, bool) or not isinstance(value, Real) for value in values):
        raise ValueError("invalid-vector")
    try:
        vector = tuple(float(value) for value in values)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("invalid-vector") from exc
    if not all(math.isfinite(value) for value in vector):
        raise ValueError("invalid-vector")
    magnitude = math.hypot(*vector)
    if magnitude == 0.0 or not math.isclose(magnitude, 1.0, rel_tol=1e-4, abs_tol=1e-4):
        raise ValueError("invalid-vector")
    return vector


def _is_supported_metadata(metadata: object) -> bool:
    return (
        type(metadata) is VectorMetadata
        and type(metadata.dimension) is int
        and metadata.dimension > 0
        and type(metadata.dtype) is str
        and metadata.dtype == "float32"
        and type(metadata.metric) is str
        and metadata.metric == "cosine"
        and type(metadata.normalization) is str
        and metadata.normalization == "l2"
        and type(metadata.provider_id) is str
        and bool(metadata.provider_id)
        and type(metadata.schema_version) is int
        and metadata.schema_version == 1
    )


__all__ = ["VectorMetadata", "validate_vector"]
