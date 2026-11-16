# Technical memo on tagging support in colorframed

State: 2026-11-16, colorframed 1.1-dev, LaTeX 2026-11-01, tagpdf 1.0i and
1.0j, framed 0.96.  Facts below were observed with pdflatex and lualatex.

The tagging support (code, tests and their tools, documentation) was written
by Claude Fable 5.2 (Anthropic) on November 12, 2026, and the `Sect` and
`Caption` structures were added the same way on November 16, 2026.

## Where the code is

- The tagging code is the last section of `colorframed.sty`.  It starts
  with `\@ifundefined{tag_mc_add_missing_to_stream:Nn}{\endinput}{}`:
  a document not using `\DocumentMetadata` reads nothing of it.
- The earlier code calls three macros which do nothing there
  (`\colorframed@artifact`, `\colorframed@tagtitle` are `\@firstofone`,
  `\colorframed@notagpara` is `\relax`).  Without `\DocumentMetadata` the
  tagging support changes nothing in the PDF.
- In a tagged document these macros of `framed.sty` are redefined:
  `\fb@put@frame`, `\fb@putboxa`, `\fb@sizeofframe`, `\TF@Title`, the
  `leftbar` environment; `\MakeFramed` gets a prefix and `\endMakeFramed`
  a suffix.

## Structure of a frame

- Requested in https://github.com/latex3/tagging-project/pull/1706: the
  same structures as tcolorbox, i.e. a `Sect` for each box and, under it,
  a `Caption` for the title.  colorframed 1.0 created no structure for a
  frame, and the title was a `P` in a `Part` before the contents.
- The `Sect` is opened by the prefix of `\MakeFramed` (after a `\par`) and
  closed by the suffix of `\endMakeFramed`.  So all environments get it,
  `leftbar` included, and also an environment defined by the user with
  `\MakeFramed`.
- Why `Sect`: tagpdf refuses a `Caption` under a `Div` which is a child of
  `Document` (a `Div` is transparent for the parent-child rules, and
  `Document` → `Caption` is not allowed).  It accepts it under `Sect` and
  under `Aside`; `Aside` would say that the frame is outside the main flow
  of the text.
- A `Sect` is accepted by tagpdf in a list item (`LBody`), in a `minipage`
  and in a float.

## Page breaks inside a frame (pdflatex only)

- With pdflatex a marked content can not cross pages; tagpdf closes and
  reopens it in the output routine, using marks.  framed splits its box
  itself with `\vsplit`, so this repair did not happen: marked content left
  open on one page, text outside marked content on the next.
- Fix: `\tag_mc_add_missing_to_stream:Nn <box> {colorframed}` on each piece
  of a split frame and on the last one.  With lualatex this command does
  nothing and nothing is needed.
- Structures are not concerned by page breaks: the `Sect` of a frame split
  across pages is one structure.
- `\tag_mc_new_stream:n` of tagpdf 1.0i creates a variable with a wrong
  name: https://github.com/latex3/tagpdf/issues/152.  The package creates
  the right one itself if it does not exist; without this, a first frame
  containing no marked content gives a TeX error.  This is fixed in tagpdf
  1.0j, with which the extra line of the package does nothing.

## Measuring

- framed executes the frame commands on a dummy box to measure the frame
  (`\fb@sizeofframe`).  This is done with tagging suspended, else a title
  containing mathematics creates structures for material which is not
  output.

## Titles (`\TitleBarFrame`, `\colorframedTitleBarFrame`)

- A title is typeset by the frame command, after the contents of the
  frame.  tagpdf has no public way to insert a structure before existing
  siblings.  So an empty `Caption` structure is created at the start of
  `\MakeFramed`, right after the `Sect` is opened, and the title is a `P`
  structure declared as its child with the `parent` key of
  `\tag_struct_begin:n`.
- Whether frame number N has a title is known from the previous
  compilation (property label `colorframed-title-N`).  In a first
  compilation the `Caption` is created when the title is typeset, hence
  is the last child of the `Sect`, and the package warns "Titles of frames
  are not at their place in the structure tree.  Rerun to get them right".
- With tcolorbox the child of the `Caption` is a `text-block` (role `P`)
  with a `TextAlign` attribute; here it is a plain `P`.
- A title may contain mathematics or `\emph` (they become `Formula` and
  `Em` children of the `P`).
- Since 1.1 `titled-frame` uses `\colorframedTitleBarFrame`, whose title is
  a paragraph in a `\vbox`: paragraph tagging is switched off there
  (`\colorframed@notagpara`), the `P` being created by the package.
- Only the title of the first piece of a frame is tagged.  The titles of
  the following pieces ("... (cont)") and all continuation marks are
  artifacts.
- An earlier implementation (commit "Tagging: titles of ...") used a
  stashed marked content and `\tag_mc_use:n`.  It failed with mathematics
  in the title (`Parent-Child 'Document' --> 'MC'`) and was replaced.
- The environments of framed.sty can not really be nested.  For the
  record: a `framed` environment inside `titled-frame` inherits the frame
  command of the latter, hence shows its title again, on the page and in
  the structure tree (as the `Caption` of its own `Sect`).

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
  in a float, in a minipage, in `multicols`, in a `twocolumn` document.
- xelatex: `test_tagging_02.tex` and `test_tagging_03.tex` compile without
  error and without parent-child warning; their PDFs were not checked.

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
- The summaries contain the structure trees: a change of the structures
  changes them, and the script then exits with status 2.
- veraPDF has not been run.
