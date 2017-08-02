topdir   := $(CURDIR)
builddir := $(topdir)/build
docdir   := $(topdir)/docs

karndir := $(realpath $(topdir)/../karn)
ifeq ($(karndir),)
$(error Invalid Karn working directory)
endif
karn_configs := $(strip\
                  $(patsubst $(karndir)/config/%.config,%,\
                    $(wildcard $(karndir)/config/*.config)))

V := 0
ifeq ($(V),0)
.SILENT:
define dologmk
	@echo $(1);
endef
endif
logmk = $(call dologmk,$(1))

.PHONY: all
all: karn-perf karn-cov karn-gh

.PHONY: karn-list_configs
karn-list_configs: $(karndir)
	$(info $(karn_configs))

.PHONY: karn-config
karn-config: $(foreach cfg,$(karn_configs),karn-config-$(cfg))

karn-config-%: clean
	$(call logmk,configuring $(@:karn-config-%=%) build) $(MAKE) \
		-C $(karndir) defconfig-$(@:karn-config-%=%) \
		BUILD=$(builddir)/$(@:karn-config-%=%)

.PHONY: karn-build
karn-build: $(foreach cfg,$(karn_configs),karn-build-$(cfg))

karn-build-%: karn-config-%
	$(call logmk,building $(@:karn-build-%=%) library) $(MAKE) \
		-C $(karndir) build \
		BUILD=$(builddir)/$(@:karn-build-%=%)

.PHONY: karn-test
karn-test: $(foreach cfg,$(karn_configs),karn-test-$(cfg))

karn-test-%: karn-build-%
	$(call logmk,building $(@:karn-test-%=%) tests) $(MAKE) \
		-C $(karndir) test \
		BUILD=$(builddir)/$(@:karn-test-%=%)

.PHONY: karn-check
karn-check: $(foreach cfg,$(karn_configs),karn-test-$(cfg))

karn-check-%: karn-test-%
	$(call logmk,running $(@:karn-check-%=%) unit tests) $(MAKE) \
		-C $(karndir) check \
		BUILD=$(builddir)/$(@:karn-check-%=%)

.PHONY: karn-data
karn-data:
	$(call logmk,building testing data sets) $(MAKE) \
		-C $(karndir) data \
		DATA=$(builddir)/data

.PHONY: karn-perf
karn-perf: $(foreach cfg,$(karn_configs),karn-test-$(cfg))

karn-perf-%: karn-test-% karn-data
	$(call logmk,running $(@:karn-perf-%=%) performance tests) $(MAKE) \
		-C $(karndir) perf \
		DATA=$(builddir)/data BUILD=$(builddir)/$(@:karn-perf-%=%)

.PHONY: karn-cov
karn-cov: $(foreach cfg,$(karn_configs),karn-check-$(cfg))

karn-cov-%: karn-check-%
	$(call logmk,building $(@:karn-cov-%=%) coverage statistics) $(MAKE) \
		-C $(karndir) cov \
		BUILD=$(builddir)/$(@:karn-cov-%=%)

.PHONY: karn-gh
karn-gh: karn-perf-all
	$(call logmk,building documentation) $(MAKE) \
		-C $(karndir) doc \
		BUILD=$(builddir)/all sphinxbuilddir=$(docdir)

.PHONY: clean
clean:
	$(RM) -r $(filter-out $(builddir)/data,$(wildcard $(builddir)/*))

.PHONY: mrproper
mrproper: clean
	$(RM) -r $(docdir)
