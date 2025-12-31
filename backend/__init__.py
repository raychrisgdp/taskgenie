"""TaskGenie backend package.

Author:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from typing import Any

__version__ = "0.1.0"


# Lazy import to avoid circular import issues
def __getattr__(name: str) -> Any:
    if name == "settings":
        from .config import get_settings  # noqa: PLC0415

        return get_settings()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["settings", "__version__"]
