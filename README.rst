placard
=======

A flake8 plugin that validates the **formatting** of Google-style
docstrings. The name is the museum-wall label affixed to the thing it
describes: short, fixed-form explanatory text, checked for shape, bound
to the artifact it annotates.

**Status:** draft design · **Prefix:** ``PLC`` · **PyPI:** ``placard``

Install
-------

.. code-block:: shell

   pip install placard

placard registers itself with flake8 via the ``flake8.extension`` entry
point. Once installed, flake8 discovers it automatically; no extra
configuration is needed to start emitting ``PLC`` codes.

Motivation
----------

``pydocstyle`` -- the de facto Google-docstring format checker, exposed
to flake8 via ``flake8-docstrings`` -- was archived in November 2023.
Its successor story routes through Ruff's ``D`` rules. placard is a
deliberately small alternative for people who want Google-docstring
*format* enforcement inside flake8 without adopting Ruff.

placard does one job: given a docstring that exists, check that it is
*shaped* the way the Google style guide demands. It does not decide
whether a docstring *should* exist, and it does not check whether a
docstring's contents are *true* about the code.

Scope
-----

In scope
^^^^^^^^

Surface conformance of docstrings that are present. Every rule is a
pure function of the string returned by ``ast.get_docstring()`` (which
applies ``inspect.cleandoc`` dedenting). No raw-source inspection, no
``tokenize``, no node-offset arithmetic.

One opinionated position: types belong in the signature
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

placard requires ``Args:`` entries in the bare ``name: description``
form and rejects ``name (type): description``. Every consumer of a
docstring that cares about types already has the signature -- IDEs,
``help()``, Sphinx autodoc, mkdocstrings, pydoc -- so a parenthesized
type in the docstring duplicates information already visible an inch
above, with the added cost of having to stay in sync.

This is the one place placard is more opinionated than the published
Google spec, which calls both forms canonical. Projects that prefer the
typed form can ``# noqa: PLC301`` on the entries that use it.

Non-goals
^^^^^^^^^

- **Presence.** placard never reports a *missing* docstring (the
  ``D100``-``D107`` family). Which definitions require docstrings is a
  separate policy, enforced elsewhere (e.g. by stolid's SLD81x).
- **Imperative mood.** A stemmer-plus-wordlist heuristic with a long
  false-positive tail. Intentionally omitted.
- **Completeness / signature agreement.** Whether every parameter
  appears under ``Args:``, whether ``Returns:`` exists iff the function
  returns a value, etc. This requires the signature and is
  **pydoclint's** job (see the seam below).
- **Quote-prefix and quote-placement rules.** ``r"""``, opening-quote
  line. These need the raw token or source slice, which
  ``get_docstring()`` discards.

The seam: placard + pydoclint
-----------------------------

Two tools, one flake8 invocation, no overlap:

- **placard** (``PLC``) -- is the docstring *shaped* correctly?
- **pydoclint** (``DOC``) -- does the docstring *agree with the code*?

A lowercase ``args:`` with a ragged body is correct-by-pydoclint,
wrong-by-placard. A perfectly formatted ``Args:`` block missing half
the parameters is correct-by-placard, wrong-by-pydoclint. The prefixes
differ, so the two compose cleanly in one flake8 run.

For a placard-aligned pydoclint setup, the following companion flags
work well::

   --style=google
   --skip-checking-short-docstrings=False
   --arg-type-hints-in-docstring=False
   --check-return-types=False
   --check-yield-types=False

``--skip-checking-short-docstrings=False`` makes pydoclint reject
description-only docstrings on functions that take arguments. The trade
is that one-line ``Returns ...`` summaries that Google style permits
also get flagged; ``# noqa`` those locally or accept the slight
over-strictness.

The remaining flags align with placard's opinion that types belong in
the signature, not the docstring.

Rule set
--------

Codes are banded by concern, leaving headroom in each band. They are
*not* a drop-in for pydocstyle's ``D`` codes.

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

The 3xx band is sub-banded by section for future-proofing:

- ``301``-``309`` -- ``Args``
- ``311``-``319`` -- ``Raises``
- ``321``-``329`` -- ``Yields``
- ``331``-``339`` -- ``Returns``
- ``341``-``349`` -- ``Attributes``

Only ``Args`` entry-shape checks ship in v1; the other slots are
reserved so future entry-shape checks can be added without renumbering.

Reporting location
------------------

All violations for a given docstring are reported at the location of
the docstring expression node (its ``lineno``/``col_offset``). The
cleaned string returned by ``ast.get_docstring`` does not preserve a
reliable mapping back to source lines (``cleandoc`` strips leading
blank lines and dedents), so placard does not try to point at
individual entries. ``# noqa: PLC...`` on the opening line of the
docstring suppresses the code for the whole docstring.

Architecture
------------

- Registered via the ``flake8.extension`` entry point under the name
  ``PLC``. No standalone CLI -- flake8 owns file discovery, the
  ``noqa`` machinery, and config plumbing.
- The plugin is a frozen ``dataclass`` with a single ``tree`` field.
  flake8 hands it the parsed ``ast``; placard walks it, and for every
  node where ``ast.get_docstring()`` returns non-``None``, runs the
  rule set against that string. Nodes with no docstring are skipped
  outright.
- **Section splitter.** In the cleaned string, a *header* is a line
  whose stripped content is exactly one of the recognized tokens; its
  *body* is the indented run beneath it until the next header or end
  of string. Strictness collapses the ambiguity that forces a
  leniency-driven tool to guess.
- **No configuration.** placard takes no flags. The convention it
  enforces is fixed at the code level; the only way to soften it is
  ``# noqa`` on the docstring's opening line.
