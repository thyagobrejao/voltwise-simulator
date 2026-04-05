"""Scenario registry.

Importing this package gives callers:

  - ``get(name)``            — retrieve a scenario coroutine by name
  - ``available_scenarios()`` — list of registered scenario names
"""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from typing import Any

from simulator.scenarios.basic import run as _basic
from simulator.scenarios.full_charge import run as _full_charge

# Map of scenario name → async coroutine function
_REGISTRY: dict[str, Callable[..., Coroutine[Any, Any, None]]] = {
    "basic": _basic,
    "full_charge": _full_charge,
}


def get(name: str) -> Callable[..., Coroutine[Any, Any, None]]:
    """Return the scenario coroutine for *name*.

    Raises:
        ValueError: If *name* is not a registered scenario.
    """
    if name not in _REGISTRY:
        available = ", ".join(sorted(_REGISTRY))
        raise ValueError(f"Unknown scenario '{name}'. Available: {available}")
    return _REGISTRY[name]


def available_scenarios() -> list[str]:
    """Return sorted list of registered scenario names."""
    return sorted(_REGISTRY)
