#!/bin/sh
dir="."

echo "Building pdf in ctanbuild/ ..."
cd $dir
latexmk -halt-on-error -interaction=batchmode colorframed-doc.tex
dvipdfmx colorframed-doc
cd ..
echo "... done"

# Local variables:
# coding: utf-8
# End:
