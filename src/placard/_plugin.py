# Flake8 plugin glue: walks the AST and yields PLC violations for each
# node whose docstring exists.

from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import Iterator

from ._rules import violations

_DOCSTRING_NODES = (
    ast.Module,
    ast.ClassDef,
    ast.FunctionDef,
    ast.AsyncFunctionDef,
)


# SLD503 (kw_only=True) is intentionally omitted: flake8 introspects
# the plugin class's positional ``__init__`` parameters via
# ``inspect.signature`` to decide which fixtures (``tree``, ``lines``,
# ``filename``, ...) to inject, and keyword-only parameters fall out of
# that lookup.
@dataclass(frozen=True, slots=True)
class Plugin:  # noqa: SLD503
    """Flake8 plugin emitting placard's ``PLC`` docstring-shape codes.

    Attributes:
        tree: The module AST flake8 hands the plugin to drive the walk.
    """

    tree: ast.AST

    def run(  # noqa: SLD303
        self,
    ) -> Iterator[tuple[int, int, str, type[Plugin]]]:
        """Walk ``self.tree`` and yield PLC violations.

        Yields:
            One ``(line, col, message, type)`` tuple per PLC violation,
            located at the offending docstring's expression node.
        """
        owner = type(self)
        for node in ast.walk(self.tree):
            if not isinstance(node, _DOCSTRING_NODES):
                continue
            text = ast.get_docstring(node)
            if text is None:
                continue
            anchor = node.body[0]
            for problem in violations(text):
                yield (
                    anchor.lineno,
                    anchor.col_offset,
                    f"{problem.code} {problem.message}",
                    owner,
                )
