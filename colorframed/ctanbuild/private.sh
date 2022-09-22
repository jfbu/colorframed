#!/bin/sh
aaa="Bu"
dir="colorframed"
bubu=" B\."
bbb="rn"
ccc="ol"
jfbu=" ${aaa}${bbb}${ccc}"

echo "Blowing up jfbu cover in README.md colorframed-doc.tex colorframed.sty ..."
sed -i "s/$bubu/$jfbu/g" "$dir/README.md"
sed -i "s/$bubu/$jfbu/g" "$dir/colorframed-doc.tex"
sed -i "s/$bubu/$jfbu/g" "$dir/colorframed.sty"
echo "... done"

# Local variables:
# coding: utf-8
# End:
