# -*- fill-column: 66; sentence-end-double-space: t -*-
docfiles    = README.md
sourcefiles = colorframed-doc.tex colorframed.sty
TEST = 

.PHONY: ctan clean

README: README.md
	pandoc -t plain -o README README.md

colorframed-doc.dvi: colorframed-doc.tex colorframed.sty
	latexmk -halt-on-error -interaction=batchmode colorframed-doc.tex

colorframed-doc.pdf: colorframed-doc.dvi
	dvipdfmx colorframed-doc.dvi

# ATTENTION à un truc comme ctanbuild/$(sourcefiles) !
# le ctanbuild/ ne s'applique qu'au premier !
colorframed.zip: $(docfiles) $(sourcefiles) ctanbuild/private.sh
	@echo 'Removing CTAN/colorframed.zip if it exists!'
	rm -fr CTAN/colorframed.zip
	rm -fr                ctanbuild/colorframed
	rm -f                 ctanbuild/colorframed.zip
	mkdir -p              ctanbuild/colorframed
	chmod ugo+rwx         ctanbuild/colorframed
	cp -a $(docfiles)     ctanbuild
	cp -a $(sourcefiles)  ctanbuild
	cd ctanbuild && ./private.sh && ./makepdf.sh
	cd ctanbuild && mv $(docfiles) $(sourcefiles) colorframed
	mv ctanbuild/colorframed-doc.pdf ctanbuild/colorframed
	cd ctanbuild && rm colorframed-doc*
	chmod -R ugo+r        ctanbuild/colorframed
	@echo 'Listing submission files'
	ls -al                ctanbuild/colorframed
	umask 0022 && cd ctanbuild && zip -r colorframed.zip colorframed
	@echo 'The colorframed.zip is ready'
	@echo '********'
	@echo 'Test coverage is non-existent, improve that!'
	@echo '********'
	mv ctanbuild/colorframed.zip CTAN/
	@echo 'New colorframed.zip now moved to CTAN/ directory.'
	@echo '********'

ctan: colorframed.zip

clean:
	rm -f colorframed-doc.dvi
	rm -f colorframed-doc.aux
	rm -f colorframed-doc.log
	rm -f colorframed-doc.out
	rm -f colorframed-doc.toc
