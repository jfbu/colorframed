#!/usr/bin/env python3
"""Print the structure tree of a tagged PDF, with the text of each MCID.

Usage: structtree.py file.pdf [--no-text] [--no-role] [--no-ref] [--pages]

Each element is printed as
    <name> [namespace] -> Standard   /T=... /Alt=...  #N  /Ref=<name>#M
where "-> Standard" is the standard type obtained through the role maps
(/RoleMapNS of PDF 2.0 namespaces, /RoleMap of the StructTreeRoot); it is
omitted when equal to the name or with --no-role.

#N is the PDF object number of the element; it is printed only for elements
which are the target of a /Ref (footnote marks and footnotes refer to each
other this way) or of the structure destination /SD of a link.  A link
annotation is printed as
    OBJR /Link /D='destination name' /SD=<name>#M
--no-ref suppresses #N, /Ref, /D and /SD.

--pages prefixes each MCID with the number of its page (p1, p2, ...).

Text is decoded with the /ToUnicode CMap of the current font when there is
one (needed for LuaLaTeX), else byte-wise (latin-1), which is enough for
T1/OT1 ASCII text.  A space is inserted for a TJ kern below -200 and for
each text positioning operator (Td, TD, T*, Tm) or new BT after some text.
"""
import re
import sys
import pikepdf

STD_NS = {
    "http://iso.org/pdf2/ssn": "pdf2",
    "http://iso.org/pdf/ssn": "pdf",
    "http://www.w3.org/1998/Math/MathML": "mathml",
}


def ns_short(uri):
    if uri is None:
        return ""
    return STD_NS.get(uri) or uri.rstrip("/").rsplit("/", 1)[-1]


def resolve_role(name, ns, root_rolemap):
    """Follow the role maps from (name, namespace dict) to a standard type.

    Returns (standard name, namespace uri); the uri is None for elements
    without namespace mapped through the PDF 1.7 /RoleMap.
    """
    seen = set()
    while True:
        uri = str(ns.NS) if ns is not None and "/NS" in ns else None
        if (name, uri) in seen:          # cycle in the role map
            return name, uri
        seen.add((name, uri))
        if uri in STD_NS:
            return name, uri
        key = "/" + name
        if ns is not None:
            rm = ns.get("/RoleMapNS")
            if rm is None or key not in rm:
                return name, uri         # unmapped non-standard name
            tgt = rm[key]
            if isinstance(tgt, pikepdf.Array):
                name, ns = str(tgt[0])[1:], tgt[1]
            else:                        # a bare name: PDF 1.7 standard type
                name, ns = str(tgt)[1:], None
                return name, None
        else:
            if root_rolemap is None or key not in root_rolemap:
                return name, None
            name = str(root_rolemap[key])[1:]


HEXPAIR_RE = re.compile(r"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]*)>")
HEXRANGE_RE = re.compile(
    r"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*(<[0-9A-Fa-f]*>|\[.*?\])", re.S)


def _utf16(hexstr):
    return bytes.fromhex(hexstr).decode("utf-16-be", "replace")


def font_decoder(font):
    """Function bytes -> str for a font dictionary."""
    tu = font.get("/ToUnicode") if isinstance(font, pikepdf.Dictionary) else None
    if tu is None:
        return lambda b: b.decode("latin-1")
    data = tu.read_bytes().decode("latin-1")
    table = {}
    for block in re.findall(r"beginbfchar(.*?)endbfchar", data, re.S):
        for a, b in HEXPAIR_RE.findall(block):
            table[int(a, 16)] = _utf16(b)
    for block in re.findall(r"beginbfrange(.*?)endbfrange", data, re.S):
        for a, b, c in HEXRANGE_RE.findall(block):
            lo, hi = int(a, 16), int(b, 16)
            if c.startswith("["):
                for i, h in enumerate(re.findall(r"<([0-9A-Fa-f]*)>", c)):
                    table[lo + i] = _utf16(h)
            elif len(c) > 2:
                h = c[1:-1]
                for i in range(hi - lo + 1):
                    table[lo + i] = _utf16(format(int(h, 16) + i, "0%dx" % len(h)))
    width = 2 if font.get("/Subtype") == "/Type0" else 1

    def decode(b):
        codes = [int.from_bytes(b[i:i + width], "big")
                 for i in range(0, len(b), width)]
        return "".join(table.get(c, chr(c) if width == 1 else "?") for c in codes)
    return decode


def page_mcid_text(pdf):
    """Map (page objgen, mcid) -> text shown inside that marked content."""
    result = {}
    decoders = {}

    def decoder_for(fonts, fname):
        font = fonts.get(fname) if fonts is not None else None
        if font is None:
            return lambda b: b.decode("latin-1")
        key = font.objgen if font.is_indirect else id(font)
        if key not in decoders:
            decoders[key] = font_decoder(font)
        return decoders[key]

    for page in pdf.pages:
        key = page.obj.objgen
        res = page.obj.get("/Resources")
        fonts = res.get("/Font") if res is not None else None
        decode = lambda b: b.decode("latin-1")
        stack = []  # list of mcid or None, one per open BDC/BMC
        for operands, op in pikepdf.parse_content_stream(page):
            name = str(op)
            if name == "Tf":
                decode = decoder_for(fonts, str(operands[0]))
                continue
            if name in ("BDC", "BMC"):
                mcid = None
                if name == "BDC" and len(operands) == 2:
                    props = operands[1]
                    if isinstance(props, pikepdf.Dictionary) and "/MCID" in props:
                        mcid = int(props.MCID)
                stack.append(mcid)
                if mcid is not None:
                    result.setdefault((key, mcid), "")
                continue
            if name == "EMC":
                if stack:
                    stack.pop()
                continue
            cur = next((m for m in reversed(stack) if m is not None), None)
            if cur is None:
                continue
            if name in ("Td", "TD", "T*", "Tm", "BT"):
                txt = result[(key, cur)]
                if txt and not txt.endswith(" "):
                    result[(key, cur)] = txt + " "
            elif name in ("Tj", "TJ", "'", '"'):
                arg = operands[-1]
                parts = []
                if isinstance(arg, pikepdf.Array):
                    for x in arg:
                        if isinstance(x, pikepdf.String):
                            parts.append(decode(bytes(x)))
                        elif float(x) < -200:
                            parts.append(" ")
                else:
                    parts.append(decode(bytes(arg)))
                result[(key, cur)] += "".join(parts)
    return result


def as_list(x):
    if x is None:
        return []
    return list(x) if isinstance(x, pikepdf.Array) else [x]


def link_action(annot):
    """(destination name or None, structure destination element or None)."""
    act = annot.get("/A")
    name = sd = None
    dest = annot.get("/Dest")
    if isinstance(act, pikepdf.Dictionary):
        dest = act.get("/D", dest)
        sdarr = act.get("/SD")
        if isinstance(sdarr, pikepdf.Array) and len(sdarr) \
                and isinstance(sdarr[0], pikepdf.Dictionary):
            sd = sdarr[0]
    if isinstance(dest, (pikepdf.String, pikepdf.Name)):
        name = str(dest)
    return name, sd


def collect_targets(root):
    """objgens of the elements pointed to by a /Ref or by a link /SD."""
    targets, seen = set(), set()

    def rec(e):
        if not isinstance(e, pikepdf.Dictionary):
            return
        if e.get("/Type") == "/OBJR":
            obj = e.get("/Obj")
            if isinstance(obj, pikepdf.Dictionary):
                sd = link_action(obj)[1]
                if sd is not None and sd.is_indirect:
                    targets.add(sd.objgen)
            return
        if "/S" not in e and e.get("/Type") != "/StructTreeRoot":
            return
        if e.is_indirect:
            if e.objgen in seen:
                return
            seen.add(e.objgen)
        for r in as_list(e.get("/Ref")):
            if isinstance(r, pikepdf.Dictionary) and r.is_indirect:
                targets.add(r.objgen)
        for k in as_list(e.get("/K")):
            rec(k)
    rec(root)
    return targets


class Walker:
    def __init__(self, pdf, show_text, show_role, show_ref=True,
                 show_pages=False):
        self.root = pdf.Root.StructTreeRoot
        self.rolemap = self.root.get("/RoleMap")
        self.texts = page_mcid_text(pdf) if show_text else {}
        self.show_text = show_text
        self.show_role = show_role
        self.show_ref = show_ref
        self.targets = collect_targets(self.root) if show_ref else set()
        self.pageno = {p.obj.objgen: i + 1 for i, p in enumerate(pdf.pages)} \
            if show_pages else None
        self.out = []
        self.seen = set()

    def elem_ref(self, e):
        s = str(e.S)[1:] if "/S" in e else "?"
        return f"<{s}>#{e.objgen[0]}" if e.is_indirect else f"<{s}>"

    def mcid_line(self, ind, mcid, page):
        txt = self.texts.get((page, mcid), "?") if page else "?"
        pg = ""
        if self.pageno is not None:
            pg = f"p{self.pageno.get(page, '?')} "
        self.out.append(ind + pg + f"MCID {mcid}"
                        + (f" {txt.strip()!r}" if self.show_text else ""))

    def walk(self, elem, depth, page):
        ind = "  " * depth
        if isinstance(elem, int) or (isinstance(elem, pikepdf.Object)
                                     and elem._type_code == pikepdf.ObjectType.integer):
            self.mcid_line(ind, int(elem), page)
            return
        if not isinstance(elem, pikepdf.Dictionary):
            return
        typ = elem.get("/Type")
        if typ == "/MCR":
            pg = elem.Pg.objgen if "/Pg" in elem else page
            if "/Stm" in elem:
                self.out.append(ind + f"MCID {int(elem.MCID)} (in XObject)")
            else:
                self.mcid_line(ind, int(elem.MCID), pg)
            return
        if typ == "/OBJR":
            line = ind + f"OBJR {elem.Obj.get('/Subtype')}"
            if self.show_ref:
                name, sd = link_action(elem.Obj)
                if name is not None:
                    line += f" /D={name!r}"
                if sd is not None:
                    line += f" /SD={self.elem_ref(sd)}"
            self.out.append(line)
            return
        s = elem.get("/S")
        if s is None:
            return
        if elem.is_indirect:
            if elem.objgen in self.seen:
                self.out.append(ind + f"<{str(s)[1:]}> (cycle!)")
                return
            self.seen.add(elem.objgen)
        if "/Pg" in elem:
            page = elem.Pg.objgen
        name = str(s)[1:]
        ns = elem.get("/NS")
        line = ind + f"<{name}>"
        uri = str(ns.NS) if ns is not None and "/NS" in ns else None
        if uri is not None:
            line += f" [{ns_short(uri)}]"
        if self.show_role:
            std, _ = resolve_role(name, ns, self.rolemap)
            if std != name:
                line += f" -> {std}"
        for key in ("/T", "/Alt", "/ActualText", "/E", "/Lang"):
            if key in elem:
                line += f" {key}={str(elem[key])!r}"
        if self.show_ref:
            if elem.is_indirect and elem.objgen in self.targets:
                line += f" #{elem.objgen[0]}"
            refs = [self.elem_ref(r) for r in as_list(elem.get("/Ref"))
                    if isinstance(r, pikepdf.Dictionary)]
            if refs:
                line += " /Ref=" + ",".join(refs)
        self.out.append(line)
        kids = elem.get("/K")
        if kids is None:
            return
        for k in (kids if isinstance(kids, pikepdf.Array) else [kids]):
            self.walk(k, depth + 1, page)


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("--")]
    if len(args) != 1:
        print(__doc__)
        return 2
    pdf = pikepdf.open(args[0])
    if "/StructTreeRoot" not in pdf.Root:
        print("No StructTreeRoot: PDF is not tagged")
        return 1
    w = Walker(pdf, "--no-text" not in argv, "--no-role" not in argv,
               "--no-ref" not in argv, "--pages" in argv)
    kids = w.root.get("/K")
    if kids is not None:
        for k in (kids if isinstance(kids, pikepdf.Array) else [kids]):
            w.walk(k, 0, None)
    print("\n".join(w.out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
