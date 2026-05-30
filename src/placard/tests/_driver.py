# Shared helpers for placard's test suite. Public names so siblings can
# do ``from ._helpers import ...`` without crossing the privacy rules.

from __future__ import annotations

import ast
import importlib.metadata


def load_plugin() -> type:
    """Return placard's ``Plugin`` class via the ``flake8.extension`` entry point.

    Returns:
        The plugin class flake8 itself would load for the ``PLC`` prefix.
    """
    eps = importlib.metadata.entry_points(group="flake8.extension")
    loaded = eps["PLC"].load()
    assert isinstance(loaded, type)
    return loaded


PLUGIN = load_plugin()


def runs(source: str) -> list[tuple[int, int, str, type]]:
    """Return every ``(line, col, message, type)`` placard yields for ``source``.

    Args:
        source: Python source whose docstrings are checked.

    Returns:
        A list of flake8-shaped tuples, in source-scan order.
    """
    return list(PLUGIN(tree=ast.parse(source)).run())


def codes(source: str) -> list[str]:
    """Return the leading ``PLCxxx`` code prefix of each violation in ``source``.

    Args:
        source: Python source whose docstrings are checked.

    Returns:
        A list of code prefixes (e.g. ``["PLC101", "PLC203"]``).
    """
    return [run[2].split()[0] for run in runs(source)]


def codes_for_doc(text: str) -> list[str]:
    """Return PLC codes placard emits for a module whose docstring is ``text``.

    Args:
        text: Docstring contents; ``cleandoc`` is applied by the AST step.

    Returns:
        A list of ``PLCxxx`` code prefixes.
    """
    return codes(f'"""{text}"""\n')


def messages_for_doc(text: str) -> list[str]:
    """Return full PLC messages placard emits for module docstring ``text``.

    Args:
        text: Docstring contents; ``cleandoc`` is applied by the AST step.

    Returns:
        A list of full ``"PLCxxx ..."`` messages.
    """
    return [run[2] for run in runs(f'"""{text}"""\n')]
