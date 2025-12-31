"""Tests for backend.__init__ module.

Author:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

import pytest


def test_backend_init_settings_attribute() -> None:
    """Test accessing settings via __getattr__ in backend.__init__."""
    import backend  # noqa: PLC0415

    # Access settings attribute (triggers __getattr__)
    settings = backend.settings
    assert settings is not None
    assert hasattr(settings, "app_name")


def test_backend_init_attribute_error() -> None:
    """Test AttributeError for non-existent attribute."""
    import backend  # noqa: PLC0415

    with pytest.raises(AttributeError, match="module 'backend' has no attribute 'nonexistent'"):
        _ = backend.nonexistent  # noqa: F841
