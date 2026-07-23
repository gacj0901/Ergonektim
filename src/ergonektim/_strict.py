"""Strict scalar and vector guards for public product boundaries."""

from __future__ import annotations

from typing import Any

import numpy as np


class StrictTypeError(ValueError):
    """Raised before a truthy value can impersonate a declared boolean."""


def require_boolean_fields(owner: str, **values: Any) -> None:
    """Require actual booleans; truthiness is not an admissible substitute."""

    invalid = sorted(
        name
        for name, value in values.items()
        if not isinstance(value, (bool, np.bool_))
    )
    if invalid:
        names = ", ".join(invalid)
        raise StrictTypeError(f"{owner} fields must be boolean: {names}")


def strict_boolean_vector(
    values: object,
    *,
    name: str,
    expected_length: int | None = None,
    require_nonempty: bool = False,
) -> np.ndarray:
    """Return a boolean view only when the incoming dtype is already boolean.

    ``numpy.asarray(..., dtype=bool)`` is deliberately forbidden here because
    nonempty strings, NaN and arbitrary nonzero numbers all become ``True``.
    """

    array = np.asarray(values)
    if array.ndim != 1:
        raise StrictTypeError(f"{name} must be a one-dimensional boolean vector")
    if require_nonempty and array.size == 0:
        raise StrictTypeError(f"{name} must be a nonempty boolean vector")
    if expected_length is not None and array.size != expected_length:
        raise StrictTypeError(f"{name} must contain {expected_length} rows")
    if array.dtype.kind != "b":
        raise StrictTypeError(
            f"{name} must have boolean dtype before validation; got {array.dtype}"
        )
    return array.astype(np.bool_, copy=False)
