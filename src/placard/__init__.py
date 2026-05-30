"""The placard flake8 plugin: Google-style docstring shape checks."""

from __future__ import annotations

import importlib.metadata

from ._plugin import Plugin

__version__ = importlib.metadata.version(__name__)
__all__ = ["Plugin", "__version__"]
