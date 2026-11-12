# Technical memo on tagging support in colorframed

State: 2026-11-12, colorframed 1.0, LaTeX 2026-11-01, tagpdf 1.0i,
framed 0.96.  Facts below were observed with pdflatex and lualatex.

The tagging support (code, tests and their tools, documentation) was written
by Claude Fable 5.2 (Anthropic) on November 12, 2026.

## Where the code is

- The tagging code is the last section of `colorframed.sty`.  It starts
  with `\@ifundefined{tag_mc_add_missing_to_stream:Nn}{\endinput}{}`:
  a document not using `\DocumentMetadata` reads nothing of it.
- The earlier code calls three macros which do nothing there
  (`\colorframed@artifact`, `\colorframed@tagtitle` are `\@firstofone`,
  `\colorframed@notagpara` is `\relax`).  Without `\DocumentMetadata` the
  PDF is byte-identical to the one obtained before tagging support.
- In a tagged document these macros of `framed.sty` are redefined:
  `\fb@put@frame`, `\fb@putboxa`, `\fb@sizeofframe`, `\TF@Title`, the
  `leftbar` environment, and `\MakeFramed` gets a prefix.

## Page breaks inside a frame (pdflatex only)

- With pdflatex a marked content can not cross pages; tagpdf closes and
  reopens it in the output routine, using marks.  framed splits its box
  itself with `\vsplit`, so this repair did not happen: marked content left
  open on one page, text outside marked content on the next.
- Fix: `\tag_mc_add_missing_to_stream:Nn <box> {colorframed}` on each piece
  of a split frame and on the last one.  With lualatex this command does
  nothing and nothing is needed.
- `\tag_mc_new_stream:n` of tagpdf 1.0i creates a variable with a wrong
  name: https://github.com/latex3/tagpdf/issues/152.  The package creates
  the right one itself if it does not exist.  Nothing has to be changed
  once tagpdf is fixed.  Without this, a first frame containing no marked
  content gives a TeX error.

## Measuring

- framed executes the frame commands on a dummy box to measure the frame
  (`\fb@sizeofframe`).  This is done with tagging suspended, else a title
  containing mathematics creates structures for material which is not
  output.

## Titles (`\TitleBarFrame`, `\colorframedTitleBarFrame`)

- A title is typeset by the frame command, after the contents of the
  frame.  tagpdf has no public way to insert a structure before existing
  siblings.  So an empty `Part` structure is created at the start of
  `\MakeFramed`, and the title is a `P` structure declared as its child
  with the `parent` key of `\tag_struct_begin:n`.
- Whether frame number N has a title is known from the previous
  compilation (property label `colorframed-title-N`).  In a first
  compilation the title is tagged after the contents, and the package
  warns "Titles of frames are not at their place in the structure tree.
  Rerun to get them right".
- A title may contain mathematics or `\emph` (they become `Formula` and
  `Em` children of the `P`).
- Only the title of the first piece of a frame is tagged.  The titles of
  the following pieces ("... (cont)") and all continuation labels are
  artifacts.
- An earlier implementation (commit "Tagging: titles of ...") used a
  stashed marked content and `\tag_mc_use:n`.  It failed with mathematics
  in the title (`Parent-Child 'Document' --> 'MC'`) and was replaced.
- A `framed` environment nested inside `titled-frame` inherits the frame
  command of the latter, hence shows its title again, on the page and in
  the structure tree.  This is framed.sty behaviour.

## Rules and coloured backgrounds

- lualatex makes all untagged material an artifact by itself.  With
  pdflatex rules outside marked content are neither tagged nor artifact.
- `\colorframed@artifact{...}` marks them in `\CustomFBox`,
  `\colorframedcolorbox`, `\colorframed@TF@Title`, `\TF@Title`, `leftbar`.
  It does nothing if a marked content is already open (use of these macros
  inside a paragraph).
- Not under the control of the package, with pdflatex:
  - the kernel leaves `tabular` rules and a bare `\hrule` outside marked
    content.  A test containing a table or such a rule needs a line
    `% XFAIL pdflatex: <reason>`;
  - a user-defined frame command built on `\fbox` or `\fcolorbox` leaves
    their rules outside marked content.

## Other observations

- lualatex: the hyphen of a word broken at a line end is an artifact, so
  the marked content of the paragraph is split there.  This happens in any
  document, with or without frames.
- These situations pass the checks with both engines: frames in a list,
  nested frames, in a float, in a minipage, in `multicols`, in a
  `twocolumn` document.

## Test tools

- `dotaggingtests.sh [pdflatex|lualatex|all] [file.tex ...]`: 7
  compilations with pdflatex, 4 with lualatex, tagpdf warnings being errors
  in the last 2, then `tagchecks.py`.  Without file argument the committed
  `test_tagging_*.tex` are used and `testsummary_<engine>.txt` is written.
- Lines in a test file: `% EXPECT: <text>` (text which must be in the
  structure tree), `% XFAIL: <reason>` or `% XFAIL <engine>: <reason>`.
- Texts of `% EXPECT:` lines should avoid the ligatures fi, fl, ff: with
  pdflatex and bitmap T1 fonts (no cm-super) they are not decoded.
- `tagchecks.py` messages: `UNBALANCED`, `UNTAGGED` (text or drawings),
  `DUPMC`, `ORPHMC`, `MISSING`, `NOTAGGED`.  Parent-child rules are checked
  by tagpdf itself.
- veraPDF has not been run.
