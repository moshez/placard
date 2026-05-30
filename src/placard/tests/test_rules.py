"""Cover every PLC rule and every branch of placard's docstring checks."""

from __future__ import annotations

import unittest

from hamcrest import assert_that, contains_string, equal_to, has_item

from ._driver import codes_for_doc, messages_for_doc


class TestSummaryRules(unittest.TestCase):
    """Cover PLC101-PLC104 against the docstring summary line."""

    def test_empty_string_raises_plc101(self) -> None:
        """An entirely empty docstring fires PLC101."""
        assert_that(codes_for_doc(""), equal_to(["PLC101"]))

    def test_whitespace_only_summary_raises_plc101(self) -> None:
        """``cleandoc`` collapses a whitespace-only docstring to empty."""
        assert_that(codes_for_doc("   "), equal_to(["PLC101"]))

    def test_summary_missing_period_raises_plc102(self) -> None:
        """A summary that doesn't end with a period fires PLC102."""
        assert_that(codes_for_doc("Summarize the thing"), equal_to(["PLC102"]))

    def test_signature_shape_raises_plc103(self) -> None:
        """A summary shaped like a call signature fires PLC103."""
        assert_that(codes_for_doc("process(data, config)."), equal_to(["PLC103"]))

    def test_prose_summary_does_not_fire_plc103(self) -> None:
        """A normal prose summary does not fire PLC103."""
        assert_that(codes_for_doc("Process the input."), equal_to([]))

    def test_no_blank_line_after_summary_raises_plc104(self) -> None:
        """A multi-line docstring without a blank line fires PLC104."""
        assert_that(
            codes_for_doc("Summarize.\nMore detail follows."),
            equal_to(["PLC104"]),
        )

    def test_blank_line_after_summary_is_clean(self) -> None:
        """A blank line after the summary satisfies PLC104."""
        assert_that(codes_for_doc("Summarize.\n\nMore detail follows."), equal_to([]))

    def test_single_line_summary_no_plc104(self) -> None:
        """A one-line docstring never triggers PLC104."""
        assert_that(codes_for_doc("Just one line."), equal_to([]))

    def test_plc103_message_includes_summary(self) -> None:
        """The PLC103 message includes the offending summary verbatim."""
        assert_that(
            messages_for_doc("connect(host, port).")[0],
            contains_string("connect(host, port)."),
        )


class TestHeaderRules(unittest.TestCase):
    """Cover PLC201-PLC204 against section header lines."""

    def test_canonical_args_header_is_clean(self) -> None:
        """An exact ``Args:`` header is accepted with a valid entry."""
        text = "Summary.\n\nArgs:\n    x: the input.\n"
        assert_that(codes_for_doc(text), equal_to([]))

    def test_unrecognized_header_raises_plc201(self) -> None:
        """A non-recognized ``Word:`` header fires PLC201."""
        text = "Summary.\n\nArguments:\n    x: the input.\n"
        assert_that(codes_for_doc(text), has_item("PLC201"))

    def test_lowercased_header_raises_plc202(self) -> None:
        """A wrong-case header (``args:``) fires PLC202."""
        text = "Summary.\n\nargs:\n    x: the input.\n"
        assert_that(codes_for_doc(text), has_item("PLC202"))

    def test_missing_colon_raises_plc203(self) -> None:
        """A bare recognized name (``Args``) fires PLC203."""
        text = "Summary.\n\nArgs\n    x: the input.\n"
        assert_that(codes_for_doc(text), has_item("PLC203"))

    def test_trailing_content_raises_plc204(self) -> None:
        """A canonical header with trailing content fires PLC204."""
        text = "Summary.\n\nArgs: some.\n    x: the input.\n"
        assert_that(codes_for_doc(text), has_item("PLC204"))

    def test_indented_word_is_not_header(self) -> None:
        """An indented ``Args:`` line is body content, not a header.

        Anchored by an unindented line so ``cleandoc`` does not dedent
        the ``Args:`` to column 0.
        """
        text = "Summary.\n\nBody paragraph.\n    Args:\n"
        assert_that(codes_for_doc(text), equal_to([]))

    def test_blank_lines_after_summary_are_ignored(self) -> None:
        """Blank body lines are not classified as headers."""
        text = "Summary.\n\n\n"
        assert_that(codes_for_doc(text), equal_to([]))

    def test_multi_word_prose_is_not_a_header(self) -> None:
        """Prose containing a colon is not flagged as a header."""
        text = "Summary.\n\nNotes about: the implementation.\n"
        assert_that(codes_for_doc(text), equal_to([]))

    def test_bare_unrecognized_word_is_not_a_header(self) -> None:
        """A bare unrecognized word at col 0 is not flagged."""
        text = "Summary.\n\nFoo\n"
        assert_that(codes_for_doc(text), equal_to([]))

    def test_lowercased_bare_name_raises_plc203(self) -> None:
        """A bare lowercase recognized name still fires PLC203."""
        text = "Summary.\n\nargs\n"
        assert_that(codes_for_doc(text), has_item("PLC203"))

    def test_canonical_returns_header_is_clean(self) -> None:
        """The other canonical headers are also accepted."""
        text = "Summary.\n\nReturns:\n    the value.\n"
        assert_that(codes_for_doc(text), equal_to([]))

    def test_canonical_attributes_header_is_clean(self) -> None:
        """``Attributes:`` is canonical because it documents instance state.

        Google style uses ``Attributes:`` in class docstrings to describe
        public instance attributes (e.g. dataclass fields), so placard
        accepts it alongside Args/Returns/Raises/Yields.
        """
        text = "Summary.\n\nAttributes:\n    x: the input.\n"
        assert_that(codes_for_doc(text), equal_to([]))

    def test_recognized_name_with_space_before_colon_passes(self) -> None:
        """``Args :`` (space before colon, no trailing content) is not flagged.

        Placard reports PLC204 only when there is real content after the
        colon; whitespace-only oddities silently pass.
        """
        text = "Summary.\n\nArgs :\n"
        assert_that(codes_for_doc(text), equal_to([]))


class TestArgsBodyRules(unittest.TestCase):
    """Cover PLC301 and PLC302 inside ``Args:`` bodies."""

    def test_valid_entry_is_clean(self) -> None:
        """A ``name: description`` entry passes."""
        text = "Summary.\n\nArgs:\n    x: the input value.\n"
        assert_that(codes_for_doc(text), equal_to([]))

    def test_empty_args_body_raises_plc302(self) -> None:
        """An ``Args:`` header with no entries fires PLC302."""
        text = "Summary.\n\nArgs:\n"
        assert_that(codes_for_doc(text), equal_to(["PLC302"]))

    def test_parenthesized_type_raises_plc301(self) -> None:
        """An entry with a parenthesized type fires PLC301."""
        text = "Summary.\n\nArgs:\n    x (int): the value.\n"
        assert_that(codes_for_doc(text), equal_to(["PLC301"]))

    def test_no_colon_in_entry_raises_plc301(self) -> None:
        """An entry without a colon fires PLC301."""
        text = "Summary.\n\nArgs:\n    just a word\n"
        assert_that(codes_for_doc(text), equal_to(["PLC301"]))

    def test_no_description_after_colon_raises_plc301(self) -> None:
        """An entry with a colon but no description fires PLC301."""
        text = "Summary.\n\nArgs:\n    x:\n"
        assert_that(codes_for_doc(text), equal_to(["PLC301"]))

    def test_no_space_after_colon_raises_plc301(self) -> None:
        """An entry must have a space between the colon and description."""
        text = "Summary.\n\nArgs:\n    x:description\n"
        assert_that(codes_for_doc(text), equal_to(["PLC301"]))

    def test_continuation_lines_do_not_double_report(self) -> None:
        """Lines deeper than the entry indent are continuations."""
        text = (
            "Summary.\n"
            "\n"
            "Args:\n"
            "    x: the value.\n"
            "        wraps across lines.\n"
            "    y: the other value.\n"
        )
        assert_that(codes_for_doc(text), equal_to([]))

    def test_blank_line_inside_body_stays_in_section(self) -> None:
        """Blank lines inside the ``Args`` body do not end the section."""
        text = (
            "Summary.\n"
            "\n"
            "Args:\n"
            "    x: the first.\n"
            "\n"
            "    y: the second.\n"
        )
        assert_that(codes_for_doc(text), equal_to([]))

    def test_body_ends_at_next_header(self) -> None:
        """A non-indented line after the body ends the Args section."""
        text = (
            "Summary.\n"
            "\n"
            "Args:\n"
            "    x: the input.\n"
            "Returns:\n"
            "    the output.\n"
        )
        assert_that(codes_for_doc(text), equal_to([]))

    def test_plc301_message_includes_offending_entry(self) -> None:
        """The PLC301 message mentions the offending entry text."""
        text = "Summary.\n\nArgs:\n    x (int): the value.\n"
        assert_that(
            messages_for_doc(text)[0],
            contains_string("x (int): the value."),
        )
