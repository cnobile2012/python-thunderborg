#
# Development by Carl J. Nobile
#

include include.mk

PREFIX		= $(shell pwd)
PACKAGE_DIR	= $(shell echo $${PWD\#\#*/})
DOCS_DIR	= $(PREFIX)/docs
TODAY		= $(shell date +"%Y-%m-%d_%H%M")
RM_REGEX	= '(^.*.pyc$$)|(^.*.wsgic$$)|(^.*~$$)|(.*\#$$)|(^.*,cover$$)'
RM_CMD		= find $(PREFIX) -regextype posix-egrep -regex $(RM_REGEX) \
                  -exec rm {} \;
PIP_ARGS	=

#----------------------------------------------------------------------
all	: tar

.PHONY	: coverage
coverage: clean
	nosetests --with-coverage --cover-erase --cover-inclusive \
                  --cover-html --cover-html-dir=$(DOCS_DIR)/htmlcov

.PHONY	: sphinx
sphinx	: clean
	(cd $(DOCS_DIR); make html)

.PHONY	: build
build	: clean
	python setup.py sdist

.PHONY	: upload
upload	: clobber
	python setup.py sdist upload -r pypi

.PHONY	: upload-test
upload-test: clobber
	python setup.py sdist upload -r pypitest

.PHONY	: install-dev
install-dev:
	pip install $(PIP_ARGS) -r requirements/development.txt

.PHONY	: install-prd
install-prd:
	pip install $(PIP_ARGS) -r requirements/production.txt


.PHONY	: tar
tar	: clean
	@(cd ..; tar -czvf $(PACKAGE_DIR).tar.gz --exclude=".git" \
          --exclude="logs/*.log" --exclude="dist/*" $(PACKAGE_DIR))

.PHONE	: build
build	: clean
	python setup.py sdist

#----------------------------------------------------------------------

clean	:
	$(shell cleanDirs.sh clean)
	@rm -rf *.egg-info
	@rm -rf python-thunderborg-1.0
	@rm -rf dist

clobber	: clean
	@(cd $(DOCS_DIR); make clobber)
	@rm logs/*.log
