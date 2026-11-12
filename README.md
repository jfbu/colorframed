# colorframed #

Repository creation date: September 20, 2022.

## Purpose ##

This is the development repository for LaTeX package
[colorframed](https://ctan.org/pkg/colorframed).

This package fixes colour leak issues which one encounters
with the environments provided by the
[framed](https://ctan.org/pkg/framed) package.

Since release 1.0 these environments can also be used in documents
producing tagged PDF (`\DocumentMetadata` with `tagging=on`), with
pdfLaTeX and LuaLaTeX.  The tagging support (code, tests and their tools,
documentation) was written by Claude (Anthropic) on November 12, 2026.

It is distributed under the LaTeX Project Public License v1.3c, see
http://www.latex-project.org/lppl.txt

## CTAN package build instructions ##

Releases (see the [tags](https://github.com/jfbu/colorframed/tags)) are pushed
to [CTAN](https://ctan.org).

To build: `cd` to `colorframed/` and execute there `make ctan`.  This produces
`colorframed.zip` to be found in the `CTAN/` sub-directory, the files
included into the archive being in the `ctanbuild/` sub-directory.

## Tagging tests ##

In `colorframed/`, `make taggingtests` compiles the files
`test_tagging_*.tex` with pdfLaTeX and LuaLaTeX and checks the tagging of the
resulting PDFs (`make dopdftaggingtests` and `make doluataggingtests` for one
engine only).  This needs Python 3 with [pikepdf](https://pypi.org/project/pikepdf/).
The results are recorded in `testsummary_pdflatex.txt` and
`testsummary_lualatex.txt`.  See `dotaggingtests.sh` for the details and
`TAGGING_MEMO.md` for technical notes on the tagging support.

## Opening a new issue ##

This is what this repo is for, so don't hesitate doing it.

*Please ping me from the created issue (with an `@jfbu` in the issue
description).* 
