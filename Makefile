#
# Development by Carl J. Nobile
#

include include.mk

PREFIX		= $(shell pwd)
PACKAGE_DIR	= $(shell echo $${PWD\#\#*/})
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
all	: tar

# $ make tests
# $ make tests TEST_PATH=tborg.tests.test_tborg.TestThunderBorg
# $ make tests TEST_PATH=tborg/tests/test_tborg.py:TestClassMethods.test_set_i2c_address_without_current_address
.PHONY	: tests
tests	: clean
	@nosetests --with-coverage --cover-erase --cover-inclusive \
                   --cover-html --cover-html-dir=$(DOCS_DIR)/htmlcov \
                   --cover-package=$(PREFIX)/tborg $(TEST_PATH)

.PHONY	: sphinx
sphinx	: clean
	(cd $(DOCS_DIR); make html)

# To add a pre-release candidate such as 'rc1' to a test package name an
# environment variable needs to be set that setup.py can read.
#
# make build TEST_TAG=rc1
# make upload-test TEST_TAG=rc1
#
# The tarball would then be named python-thunderborg-2.0.0rc1.tar.gz
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

.PHONY	: tar
tar	: clean
	@(cd ..; tar -czvf $(PACKAGE_DIR).tar.gz --exclude=".git" \
          --exclude="$(LOGS_DIR)/*.log" --exclude="dist/*" $(PACKAGE_DIR))

#----------------------------------------------------------------------

clean	:
	$(shell $(RM_CMD))

clobber	: clean
	@rm -rf dist build *.egg-info
	@rm -rf $(DOCS_DIR)/htmlcov
	@rm -rf $(DOCS_DIR)/build
