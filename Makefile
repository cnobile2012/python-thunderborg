#
# Development by Carl J. Nobile
#

include include.mk

PREFIX		= $(shell pwd)
BASE_DIR	= $(shell basename $(PREFIX))
PACKAGE_DIR	= $(BASE_DIR)-$(VERSION)$(TEST_TAG)
DOCS_DIR	= $(PREFIX)/docs
LOGS_DIR	= $(PREFIX)/logs
TODAY		= $(shell date +"%Y-%m-%d_%H%M")
RM_REGEX	= '(^.*.pyc$$)|(^.*.wsgic$$)|(^.*~$$)|(.*\#$$)|(^.*,cover$$)'
RM_CMD		= find $(PREFIX) -regextype posix-egrep -regex $(RM_REGEX) \
                  -exec rm {} \;
TEST_TAG        =
PIP_ARGS	= # Pass var for pip install.
TEST_PATH	= # Pass var for test paths.

#----------------------------------------------------------------------
all	: help

#----------------------------------------------------------------------
.PHONY:	help
help	:
	@LC_ALL=C $(MAKE) -pRrq -f $(firstword $(MAKEFILE_LIST)) : \
                2>/dev/null | awk -v RS= \
                -F: '/(^|\n)# Files(\n|$$)/,/(^|\n)# Finished Make data \
                     base/ {if ($$1 !~ "^[#.]") {print $$1}}' | sort | grep \
                -E -v -e '^[^[:alnum:]]' -e '^$@$$'

#
# The tarball would then be named python-thunderborg-2.0.0rc1.tar.gz
#
.PHONY	: tar
tar	: clean
	@(cd ..; tar -czvf $(PACKAGE_DIR).tar.gz --exclude=".git" \
          --exclude="__pycache__" --exclude="$(LOGS_DIR)/*.log" \
          --exclude="dist/*" $(BASE_DIR))

#----------------------------------------------------------------------
# $ make tests
# $ make tests TEST_PATH=tborg/tests/test_tborgpy::TestThunderBorg
# $ make tests TEST_PATH=tborg/tests/test_tborg.py::TestClassMethods::test_set_i2c_address_without_current_address
.PHONY	: tests
tests	: clean
	@rm -rf $(DOCS_DIR)/htmlcov
	@mkdir -p $(LOGS_DIR)
	@coverage erase --rcfile=$(COVERAGE_FILE)
        # The --omit must be here or tests will be in coverage.
	@coverage run --rcfile=$(COVERAGE_FILE) --omit="tborg/tests/*" -m pytest \
         --capture=tee-sys $(TEST_PATH)
	@coverage report -m --rcfile=$(COVERAGE_FILE)
	@coverage html --rcfile=$(COVERAGE_FILE)
	@echo $(TODAY)

.PHONY	: flake8
flake8	:
        # Error on syntax errors or undefined names.
	flake8 . --select=E9,F7,F63,F82 --show-source
        # Warn on everything else.
	flake8 . --exit-zero

.PHONY	: sphinx
sphinx	: clean
	(cd $(DOCS_DIR); make html)

# To add a pre-release candidate such as 'rc1' to a test package name an
# environment variable needs to be set that setup.py can read.
#
# make build TEST_TAG=rc1
# make upload-test TEST_TAG=rc1
#
.PHONY	: build
build   : export PR_TAG=$(TEST_TAG)
build	: clean
	python setup.py sdist

.PHONY	: upload
upload	: clobber
	python setup.py sdist
	python setup.py bdist_wheel --universal
	twine upload --repository pypi dist/*

.PHONY	: upload-test
upload-test: clobber build
	python setup.py bdist_wheel --universal
	twine upload --repository testpypi dist/*

.PHONY	: install-dev
install-dev:
	pip install $(PIP_ARGS) -r requirements/development.txt

.PHONY	: install-prd
install-prd:
	pip install $(PIP_ARGS) -r requirements/production.txt

#----------------------------------------------------------------------

clean	:
	$(shell $(RM_CMD))

clobber	: clean
	@rm -rf dist build *.egg-info
	@rm -rf $(DOCS_DIR)/htmlcov
	@rm -rf $(DOCS_DIR)/build
