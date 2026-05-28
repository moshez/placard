"""Cover the flake8 plugin entry point that drives placard's rules."""

from __future__ import annotations

import ast
import unittest

from hamcrest import assert_that, contains_string, equal_to, has_item

from .._plugin import Plugin


def _runs(
    tree: ast.AST,
) -> list[tuple[int, int, str, type[Plugin]]]:
    return list(Plugin(tree=tree).run())


def _codes_in(source: str) -> list[str]:
    return [run[2].split()[0] for run in _runs(ast.parse(source))]


def _first_run(source: str) -> tuple[int, int, str, type[Plugin]]:
    return _runs(ast.parse(source))[0]


class TestPluginDispatch(unittest.TestCase):
    """Plugin.run walks the AST and emits PLC violations for docstrings."""

    def test_module_docstring_line_and_code(self) -> None:
        """A module docstring violation reports at line 1 with its code."""
        first = _first_run('"""bad summary"""\n')
        assert_that(first[0], equal_to(1))
        assert_that(first[2], contains_string("PLC102"))

    def test_function_docstring_violations_emitted(self) -> None:
        """A function docstring is checked just like a module docstring."""
        source = 'def f():\n    """bad summary"""\n    return 1\n'
        assert_that(_codes_in(source), has_item("PLC102"))

    def test_class_docstring_violations_emitted(self) -> None:
        """A class docstring is checked."""
        source = 'class C:\n    """bad summary"""\n    pass\n'
        assert_that(_codes_in(source), has_item("PLC102"))

    def test_async_function_docstring_violations_emitted(self) -> None:
        """An async function docstring is checked."""
        source = 'async def f():\n    """bad summary"""\n    return 1\n'
        assert_that(_codes_in(source), has_item("PLC102"))

    def test_missing_docstring_is_skipped(self) -> None:
        """A function without a docstring produces no output."""
        source = "def f():\n    return 1\n"
        assert_that(_codes_in(source), equal_to([]))

    def test_good_docstring_produces_no_violations(self) -> None:
        """A well-formed docstring produces no violations."""
        source = 'def f():\n    """Do the thing."""\n    return 1\n'
        assert_that(_codes_in(source), equal_to([]))

    def test_yielded_class_is_plugin(self) -> None:
        """The fourth tuple element is the Plugin class itself."""
        first = _first_run('"""bad"""\n')
        assert_that(first[3], equal_to(Plugin))

    def test_nested_function_docstring_is_checked(self) -> None:
        """Docstring rules apply to functions nested inside other nodes."""
        source = (
            "def outer():\n"
            "    def inner():\n"
            '        """bad summary"""\n'
            "        return 1\n"
            "    return inner\n"
        )
        assert_that(_codes_in(source), has_item("PLC102"))

    def test_column_matches_docstring_col_offset(self) -> None:
        """The reported column equals the docstring node's col_offset."""
        first = _first_run('def f():\n    """bad"""\n    return 1\n')
        assert_that(first[1], equal_to(4))
