#!/bin/bash

# ================ FAIRE git diff APRÈS ================

YYYYo="2026"
MMo="11"
DDo="16"
VERSIONo="1.1"

# adapter au prochain bump
YYYY="2026"
MM="12"
DD="31"
VERSION="1.2-dev"

# ================ FAIRE git diff APRÈS ================

# d'après 
# https://robots.thoughtbot.com/sed-102-replace-in-place
# peut-être il faut sed -i'' sur certains systèmes.
# mais ok sur mon MBA et aussi sur Ubuntu pour sed -i

# on pourrait utiliser avec -i.bak mais de toute façon
# il y a git diff pour contrôler.

sed -i "s|Release $VERSIONo of $YYYYo/$MMo/$DDo|Release $VERSION of $YYYY/$MM/$DD|" colorframed-doc.tex
sed -i "s|$YYYYo/$MMo/$DDo v$VERSIONo|$YYYY/$MM/$DD v$VERSION|" colorframed.sty
sed -i "s|% colorframed $VERSIONo|% colorframed $VERSION|" README.md
sed -i "s|% $YYYYo/$MMo/$DDo|% $YYYY/$MM/$DD|" README.md


# ================ FAIRE git diff APRÈS ================

echo "******** VÉRIFIER ANNÉES DE COPYRIGHT ********"
echo "******** FAIRE git diff ********"
