placard
=======

A flake8 plugin that validates the **formatting** of Google-style
docstrings. The name is the museum-wall label affixed to the thing it
describes: short, fixed-form explanatory text, checked for shape, bound
to the artifact it annotates.

Install
-------

.. code-block:: shell

   pip install placard

placard registers itself with flake8 via the ``flake8.extension`` entry
point. Once installed, flake8 discovers it automatically; no extra
configuration is needed to start emitting ``PLC`` codes.

What it checks
--------------

placard does one job: given a docstring that exists, check that it is
*shaped* the way the Google style guide demands. It does not decide
whether a docstring *should* exist, and it does not check whether the
docstring's contents are *true* about the code.

============ ========== ====================================================
Code         Band       Rule
============ ========== ====================================================
``PLC101``   summary    Summary line is empty
``PLC102``   summary    Summary line does not end with a period
``PLC103``   summary    Summary line restates the function signature
``PLC104``   summary    Multi-line docstring has no blank line after summary
``PLC201``   section    Unrecognized section header
``PLC202``   section    Recognized section header with incorrect case
``PLC203``   section    Recognized section header missing its trailing colon
``PLC204``   section    Section header has trailing content after the colon
``PLC301``   args       ``Args:`` entry is not in ``name: description`` form
``PLC302``   args       ``Args:`` section is present but empty
============ ========== ====================================================

Recognized section headers: ``Args:``, ``Attributes:``, ``Raises:``,
``Returns:``, ``Yields:``. ``Attributes:`` is included because Google
style uses it in class docstrings to document instance attributes
(e.g. dataclass fields), using the same ``name: description`` shape as
``Args:`` entries.

Types belong in the signature
-----------------------------

placard requires ``Args:`` entries in the bare ``name: description``
form and rejects ``name (type): description``. Every consumer of a
docstring that cares about types already has the signature -- IDEs,
``help()``, Sphinx autodoc, mkdocstrings, pydoc -- so a parenthesized
type in the docstring duplicates information already visible an inch
above, with the added cost of having to stay in sync.

This is the one place placard is more opinionated than the published
Google spec, which calls both forms canonical. Projects that prefer the
typed form can ``# noqa: PLC301`` on the entries that use it.

Works with pydoclint
--------------------

Two tools, one flake8 invocation, no overlap:

- **placard** (``PLC``) -- is the docstring *shaped* correctly?
- **pydoclint** (``DOC``) -- does the docstring *agree with the code*?

A lowercase ``args:`` with a ragged body is correct-by-pydoclint,
wrong-by-placard. A perfectly formatted ``Args:`` block missing half
the parameters is correct-by-placard, wrong-by-pydoclint. The prefixes
differ, so the two compose cleanly in one flake8 run.

A placard-aligned pydoclint invocation::

   pydoclint \
       --style=google \
       --skip-checking-short-docstrings=False \
       --arg-type-hints-in-docstring=False \
       --check-return-types=False \
       --check-yield-types=False \
       src/

``--skip-checking-short-docstrings=False`` makes pydoclint reject
description-only docstrings on functions that take arguments; the
remaining flags align with placard's opinion that types belong in the
signature, not the docstring.
