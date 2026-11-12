#!/usr/bin/env python3
"""Generic sanity checks on the marked content of a tagged PDF.

Usage: tagchecks.py [--list] [--expect TEXT]... file.pdf ...

Needs structtree.py in the same directory (text extraction, role maps).

  NOTAGGED   the PDF has no structure tree
  UNBALANCED in a page, a marked content is opened and not closed, or closed
             without having been opened (BDC/BMC and EMC operators); typical
             of a paragraph split by other means than the output routine
             with pdflatex
  UNTAGGED   text in a page outside of any marked content (neither tagged
             nor artifact)
  DUPMC      a marked content (page, MCID) referenced more than once by the
             structure tree
  ORPHMC     a marked content with MCID in a page which is not referenced by
             the structure tree
  MISSING    a text given by --expect is not found in the text of the
             structure tree (spaces are ignored in the comparison); this
             detects text which was made an artifact
  COUNT      numbers of structures and of marked contents referenced by the
             structure tree (always printed)

With --list, the structure tree is printed before the messages, one line
per structure and per marked content, the text of the latter being cut
after 30 characters.

Parent-child legality itself is checked by tagpdf, not here.

Exit status: 0 if only the structure tree and the COUNT line were printed,
1 if there was any other message, 2 for a usage error, 3 if pikepdf is not
available (nothing checked).
"""
import sys
try:
    import pikepdf
except ImportError:
    print("tagchecks.py: pikepdf is not available, no check done")
    sys.exit(3)
from structtree import Walker, as_list, page_mcid_text

TEXTOPS = ("Tj", "TJ", "'", '"')
CUT = 30


def is_int(x):
    return isinstance(x, int) or (isinstance(x, pikepdf.Object)
                                  and x._type_code == pikepdf.ObjectType.integer)


def is_elem(x):
    return isinstance(x, pikepdf.Dictionary) and "/S" in x


def page_scan(pdf):
    """List of (page number, unclosed, unopened, untagged text operators)."""
    out = []
    for i, page in enumerate(pdf.pages):
        depth = unopened = untagged = 0
        for operands, op in pikepdf.parse_content_stream(page):
            name = str(op)
            if name in ("BDC", "BMC"):
                depth += 1
            elif name == "EMC":
                if depth:
                    depth -= 1
                else:
                    unopened += 1
            elif depth == 0 and name in TEXTOPS:
                untagged += 1
        out.append((i + 1, depth, unopened, untagged))
    return out


class ShortWalker(Walker):
    """Structure tree with pages and with the text cut after CUT characters."""

    def mcid_line(self, ind, mcid, page):
        txt = " ".join(self.texts.get((page, mcid), "?").split()) if page else "?"
        if len(txt) > CUT:
            txt = txt[:CUT] + "..."
        self.out.append(ind + f"p{self.pageno.get(page, '?')} MCID {mcid} {txt!r}")


def check(path, listing, expected):
    pdf = pikepdf.open(path)
    root = pdf.Root.get("/StructTreeRoot")
    if root is None:
        return ["NOTAGGED"]
    texts = page_mcid_text(pdf)
    pageno = {p.obj.objgen: i + 1 for i, p in enumerate(pdf.pages)}

    nstruct = 0
    allmc = []
    guard = set()

    def rec(e, page):
        nonlocal nstruct
        if e.is_indirect:
            if e.objgen in guard:
                return
            guard.add(e.objgen)
        nstruct += 1
        if "/Pg" in e:
            page = e.Pg.objgen
        for k in as_list(e.get("/K")):
            if is_int(k):
                allmc.append((page, int(k)))
            elif not isinstance(k, pikepdf.Dictionary):
                continue
            elif k.get("/Type") == "/MCR":
                if "/Stm" not in k:
                    allmc.append((k.Pg.objgen if "/Pg" in k else page,
                                  int(k.MCID)))
            elif "/S" in k:
                rec(k, page)

    for k in as_list(root.get("/K")):
        if is_elem(k):
            rec(k, None)

    lines, msgs = [], []
    if listing:
        w = ShortWalker(pdf, True, True, False, True)
        for k in as_list(root.get("/K")):
            w.walk(k, 0, None)
        lines = w.out

    for pg, unclosed, unopened, untagged in page_scan(pdf):
        if unclosed or unopened:
            msgs.append(f"UNBALANCED p{pg}: {unclosed} marked content(s) not "
                        f"closed, {unopened} closed without being opened")
        if untagged:
            msgs.append(f"UNTAGGED p{pg}: {untagged} text operator(s) outside "
                        f"marked content")

    seen, dups = set(), []
    for c in allmc:
        if c in seen and c not in dups:
            dups.append(c)
        seen.add(c)

    def mclist(items):
        shown = ", ".join(f"p{pageno.get(p, '?')} MCID {m}"
                          for p, m in items[:10])
        return shown + (f" (and {len(items) - 10} more)"
                        if len(items) > 10 else "")

    if dups:
        msgs.append(f"DUPMC   {len(dups)} marked content(s): {mclist(dups)}")
    orphans = sorted((c for c in texts if c not in seen),
                     key=lambda c: (pageno.get(c[0], 0), c[1]))
    if orphans:
        msgs.append(f"ORPHMC  {len(orphans)} marked content(s): "
                    f"{mclist(orphans)}")

    tagged = "".join("".join(texts.get(c, "").split()) for c in allmc)
    for t in expected:
        if "".join(t.split()) not in tagged:
            msgs.append(f"MISSING {t!r} is not in the text of the structure "
                        f"tree")

    out = lines + msgs
    out.append(f"COUNT   {nstruct} structure(s), {len(seen)} marked "
               f"content(s)")
    return out


def main(argv):
    paths, expected, listing = [], [], False
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--list":
            listing = True
        elif a == "--expect":
            i += 1
            if i == len(argv):
                print(__doc__)
                return 2
            expected.append(argv[i])
        elif a.startswith("--"):
            print(__doc__)
            return 2
        else:
            paths.append(a)
        i += 1
    if not paths:
        print(__doc__)
        return 2
    status = 0
    for p in paths:
        print(f"=== {p}")
        for m in check(p, listing, expected):
            print("  " + m)
            if m.startswith(("NOTAGGED", "UNBALANCED ", "UNTAGGED ", "DUPMC ",
                             "ORPHMC ", "MISSING ")):
                status = 1
    return status


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
