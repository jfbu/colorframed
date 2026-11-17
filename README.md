# colorframed #

## Purpose ##

This is the development repository for LaTeX package
[colorframed](https://ctan.org/pkg/colorframed).

**Please ping me from any created issue (with an `@jfbu` in the issue
description) else I will NOT become aware of it.**

This package was initially released in September 2022 to
fix the colour leak issues which one encounters
with the environments provided by the
[framed](https://ctan.org/pkg/framed) package.

Since release 1.0 of 2026/11/12 these environments can also be used in
documents producing tagged PDF.

The package is distributed under the LaTeX Project Public License v1.3c, see
http://www.latex-project.org/lppl.txt

## CTAN package build instructions ##

Releases (see the [tags](https://github.com/jfbu/colorframed/tags)) are pushed
to [CTAN](https://ctan.org).

To only build the PDF documentation execute `make doc` from inside `colorframed/`.

To build the full `colorframed.zip` as used for `CTAN` uploads, execute `make
ctan` in `colorframed/`.  The `colorframed.zip` will be found in
`colorframed/CTAN/`.


## Tagging tests ##

In `colorframed/`, `make taggingtests` compiles the files
`test_tagging_*.tex` with pdfLaTeX and LuaLaTeX and checks the tagging of the
resulting PDFs (`make pdftaggingtests` and `make luataggingtests` for one
engine only).  This needs Python 3 with [pikepdf](https://pypi.org/project/pikepdf/).
The results are recorded in `testsummary_pdflatex.txt` and
`testsummary_lualatex.txt`.  See `dotaggingtests.sh` for the details and
`TAGGING_MEMO.md` for technical notes on the tagging support.

The tagging checks are not done by a full validator and are only indicative.

The testing infrastructure is based upon the one originally developed in 2024-2025
by the author for the [jfbu/etoc](https://github.com/jfbu/etoc) project, which
was later (in November 2026) enriched with Python scripts (requiring
[pikepdf](https://pypi.org/project/pikepdf/)) checking the PDF structures.
Those were provided by AI assistance.
