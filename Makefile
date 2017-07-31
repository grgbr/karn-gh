topdir   := $(CURDIR)
srcdir   := $(topdir)/karn
builddir := $(topdir)/build
docdir   := $(topdir)/docs

.PHONY: gh
gh: | $(srcdir)
	cd $(srcdir) && git pull
	$(MAKE) -C $(srcdir) doc BUILD=$(builddir) sphinxbuilddir=$(docdir)

$(srcdir):
	git clone --depth 1 https://github.com/grgbr/karn.git

.PHONY: clean
clean:
	$(RM) -r  $(srcdir) $(builddir)

.PHONY: mrproper
mrproper: clean
	$(RM) -r $(docdir)
