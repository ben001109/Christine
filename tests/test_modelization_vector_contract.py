import math

import pytest

from christine.modelization import VectorMetadata as ExportedVectorMetadata
from christine.modelization import validate_vector as exported_validate_vector
from christine.modelization.vector_contract import VectorMetadata, validate_vector


def test_validates_normalized_finite_vector():
    metadata = VectorMetadata(2, "float32", "cosine", "l2", "local-test")
    assert validate_vector([0.6, 0.8], metadata) == (0.6, 0.8)


@pytest.mark.parametrize(
    "values",
    [
        [],
        [1.0],
        [math.nan, 0.0],
        [math.inf, 0.0],
        [0.0, 0.0],
        [1.0, 1.0],
        [True, False],
        ["0.6", "0.8"],
        [1e308, 0.0],
    ],
)
def test_rejects_wrong_dimension_non_finite_zero_or_non_normalized_vector(values):
    metadata = VectorMetadata(2, "float32", "cosine", "l2", "local-test")
    with pytest.raises(ValueError, match="^invalid-vector$"):
        validate_vector(values, metadata)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"dimension": 0},
        {"dtype": "float64"},
        {"metric": "dot"},
        {"normalization": "none"},
        {"provider_id": ""},
        {"schema_version": 0},
        {"schema_version": True},
        {"dtype": object()},
    ],
)
def test_metadata_is_fail_closed(kwargs):
    values = {"dimension": 2, "dtype": "float32", "metric": "cosine", "normalization": "l2", "provider_id": "local-test"}
    values.update(kwargs)
    with pytest.raises(ValueError, match="^invalid-vector-metadata$"):
        VectorMetadata(**values)


def test_rejects_a_forged_metadata_instance_before_reading_vector_values():
    forged = object.__new__(VectorMetadata)
    object.__setattr__(forged, "dimension", 2)
    object.__setattr__(forged, "dtype", "float32")
    object.__setattr__(forged, "metric", "cosine")
    object.__setattr__(forged, "normalization", "l2")
    object.__setattr__(forged, "provider_id", "local-test")
    object.__setattr__(forged, "schema_version", 99)

    with pytest.raises(ValueError, match="^invalid-vector$"):
        validate_vector([0.6, 0.8], forged)


def test_modelization_package_exports_vector_contract_public_api():
    assert ExportedVectorMetadata is VectorMetadata
    assert exported_validate_vector is validate_vector
