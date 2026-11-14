docfiles    = README.md
sourcefiles = colorframed-doc.tex colorframed.sty
TEST = 

.PHONY: doc ctan clean pdftaggingtests luataggingtests taggingtests

README: README.md
	pandoc -t plain -o README README.md

colorframed-doc.dvi: colorframed-doc.tex colorframed.sty
	latexmk -halt-on-error -interaction=batchmode colorframed-doc.tex

colorframed-doc.pdf: colorframed-doc.dvi
	dvipdfmx colorframed-doc.dvi

doc: colorframed-doc.pdf README

# ATTENTION à un truc comme ctanbuild/$(sourcefiles) !
# le ctanbuild/ ne s'applique qu'au premier !
colorframed.zip: $(docfiles) $(sourcefiles) ctanbuild/private.sh ctanbuild/makepdf.sh
	@echo 'Removing CTAN/colorframed.zip if it exists!'
	rm -fr CTAN/colorframed.zip
	rm -fr                ctanbuild/colorframed
	rm -f                 ctanbuild/colorframed.zip
	mkdir -p              ctanbuild/colorframed
	chmod ugo+rwx         ctanbuild/colorframed
	cp -a $(docfiles)     ctanbuild/
	cp -a $(sourcefiles)  ctanbuild/
	cd ctanbuild && ./private.sh && ./makepdf.sh
	cd ctanbuild && mv $(docfiles) $(sourcefiles) colorframed/
	mv ctanbuild/colorframed-doc.pdf ctanbuild/colorframed/
	cd ctanbuild && rm colorframed-doc*
	chmod -R ugo+r        ctanbuild/colorframed
	@echo 'Listing submission files'
	ls -al                ctanbuild/colorframed
	umask 0022 && cd ctanbuild && zip -r colorframed.zip colorframed
	@echo 'The colorframed.zip is ready'
	@echo '********'
	@echo 'Consider running the tagging tests, if not already done'
	@echo '********'
	@echo 'General test coverage is non-existent, improve that!'
	@echo '********'
	mv ctanbuild/colorframed.zip CTAN/
	@echo 'New colorframed.zip now moved to CTAN/ directory.'
	@echo 'Think hard and recall how you proceed from here,'
	@echo 'without pushing it to GitHub (cf secret diary).'
	@echo '********'

# Let it also create the pdf in the working directory to avoid confusion.
ctan: doc colorframed.zip

pdftaggingtests:
	./dotaggingtests.sh pdflatex

luataggingtests:
	./dotaggingtests.sh lualatex

taggingtests:
	./dotaggingtests.sh all

clean:
	rm -f colorframed-doc.dvi
	rm -f colorframed-doc.aux
	rm -f colorframed-doc.log
	rm -f colorframed-doc.out
	rm -f colorframed-doc.toc
	rm -f colorframed-doc.fdb_latexmk
	rm -f colorframed-doc.fls
