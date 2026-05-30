# Pure docstring-shape checks. Every function takes the cleaned string
# returned by ``ast.get_docstring(node)`` (or a derived view of it) and
# yields PLC violations without consulting the AST or raw source.

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterator

RECOGNIZED = frozenset({"Args", "Attributes", "Raises", "Returns", "Yields"})
_RECOGNIZED_LOWER: frozenset[str] = frozenset(label.lower() for label in RECOGNIZED)
_CANONICAL_HEADERS: frozenset[str] = frozenset(f"{label}:" for label in RECOGNIZED)
_CANONICAL_ARGS = "Args:"

_SIGNATURE_LIKE = re.compile(r"^[A-Za-z_]\w*\(")
_PURE_WORD = re.compile(r"^[A-Za-z]+$")
_VALID_ARGS_ENTRY = re.compile(r"^[^():]*?[^():\s][^():]*?: \S")


@dataclass(frozen=True, slots=True, kw_only=True)
class Violation:
    """A placard rule violation produced by the docstring checks.

    Attributes:
        code: The ``PLCxxx`` identifier (e.g. ``PLC101``).
        message: Human-readable description of what is wrong.
    """

    code: str
    message: str


def violations(text: str) -> Iterator[Violation]:
    """Yield every PLC violation in cleaned docstring ``text``.

    Args:
        text: The cleaned docstring (as returned by ``ast.get_docstring``).

    Yields:
        One :class:`Violation` per defect found, in source-scan order.
    """
    cleaned_lines = tuple(text.splitlines())
    yield from _summary_violations(cleaned_lines)
    yield from _header_violations(cleaned_lines)
    for body in _args_bodies(cleaned_lines):
        yield from _args_body_violations(body)


def _summary_violations(
    cleaned_lines: tuple[str, ...],
) -> Iterator[Violation]:
    if not cleaned_lines:
        yield Violation(code="PLC101", message="Summary is empty")
        return
    summary = cleaned_lines[0]
    if not summary.endswith("."):
        yield Violation(
            code="PLC102",
            message="Summary lacks trailing period",
        )
    if _SIGNATURE_LIKE.match(summary):
        yield Violation(
            code="PLC103",
            message=f"Summary mirrors signature: {summary!r}",
        )
    if len(cleaned_lines) > 1 and cleaned_lines[1].strip():
        yield Violation(
            code="PLC104",
            message="Missing blank line after summary",
        )


def _header_violations(
    cleaned_lines: tuple[str, ...],
) -> Iterator[Violation]:
    for entry in cleaned_lines[1:]:
        if entry != entry.lstrip():
            continue
        defect = _header_defect(entry.rstrip())
        if defect is not None:
            yield defect


def _header_defect(stripped: str) -> Violation | None:
    if not stripped or stripped in _CANONICAL_HEADERS:
        return None
    head, sep, tail = stripped.partition(":")
    label = head.strip()
    if not _PURE_WORD.match(label):
        return None
    if sep == "":
        return _bare_word_defect(label, stripped)
    return _colon_form_defect(label, tail, stripped)


def _bare_word_defect(label: str, stripped: str) -> Violation | None:
    if label.lower() not in _RECOGNIZED_LOWER:
        return None
    return Violation(
        code="PLC203",
        message=f"Section header missing colon: {stripped!r}",
    )


def _colon_form_defect(label: str, tail: str, stripped: str) -> Violation | None:
    if label in RECOGNIZED:
        if tail.strip():
            return Violation(
                code="PLC204",
                message=f"Section header trailing content: {stripped!r}",
            )
        return None
    if label.lower() in _RECOGNIZED_LOWER:
        return Violation(
            code="PLC202",
            message=f"Section header wrong case: {stripped!r}",
        )
    return Violation(
        code="PLC201",
        message=f"Unrecognized section header: {stripped!r}",
    )


def _args_bodies(
    cleaned_lines: tuple[str, ...],
) -> Iterator[tuple[str, ...]]:
    cursor = 1
    while cursor < len(cleaned_lines):
        entry = cleaned_lines[cursor]
        cursor += 1
        if entry != entry.lstrip() or entry.rstrip() != _CANONICAL_ARGS:
            continue
        body_start = cursor
        while cursor < len(cleaned_lines) and _is_body_member(cleaned_lines[cursor]):
            cursor += 1
        yield cleaned_lines[body_start:cursor]


def _is_body_member(entry: str) -> bool:
    if not entry.strip():
        return True
    return entry != entry.lstrip()


def _args_body_violations(body: tuple[str, ...]) -> Iterator[Violation]:
    nonblank = tuple(entry for entry in body if entry.strip())
    if not nonblank:
        yield Violation(
            code="PLC302",
            message="Args section is empty",
        )
        return
    base_indent = min(len(entry) - len(entry.lstrip()) for entry in nonblank)
    for entry in nonblank:
        current_indent = len(entry) - len(entry.lstrip())
        if current_indent != base_indent:
            continue
        content = entry.lstrip()
        if _VALID_ARGS_ENTRY.match(content) is None:
            yield Violation(
                code="PLC301",
                message=f"Args entry malformed: {content!r}",
            )
