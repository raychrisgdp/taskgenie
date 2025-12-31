"""Tests for schemas __init__ module.

Author:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""


def test_schemas_init() -> None:
    """Test schemas __init__ module."""
    import backend.schemas  # noqa: PLC0415

    assert backend.schemas.__all__ == []
