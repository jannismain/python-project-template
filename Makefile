.PHONY: install
install: ## install all dependencies & development requirements
	@pip install -e .[dev,test,doc]

PUBLISHED_EXAMPLES = build/examples/github build/examples/gitlab build/examples/gitlab_sphinx
DOC_EXAMPLES = docs/examples/mkdocs docs/examples/sphinx docs/examples/default docs/examples/minimal docs/examples/full docs/examples/gitlab

.PHONY: examples $(PUBLISHED_EXAMPLES) example-setup example-setup-commit example-setup-local example examples-clean

examples: ## build all published examples
examples: $(PUBLISHED_EXAMPLES)

INIT_PYTHON_PROJECT_ARGS=--project-name="Sample Project"
build/examples/%: EXAMPLE_DIR:=$@ INIT_PYTHON_PROJECT_ARGS+=--user-name=jannismain
build/examples/github: INIT_PYTHON_PROJECT_ARGS+=--remote=github --remote-url=git@github.com:jannismain/python-project-template-example.git
build/examples/gitlab%: INIT_PYTHON_PROJECT_ARGS+=--remote=gitlab
build/examples/gitlab: INIT_PYTHON_PROJECT_ARGS+=--remote-url=git@gitlab.com:jannismain/python-project-template-example.git
build/examples/gitlab_sphinx: INIT_PYTHON_PROJECT_ARGS+=--remote-url=git@gitlab.com:jannismain/python-project-template-example-sphinx.git --docs=sphinx

$(PUBLISHED_EXAMPLES): uncopy-template link-template
	@echo "Recreating '$@'..."
	@rm -rf "$@" && mkdir -p "$@"
	init-python-project "$@" ${INIT_PYTHON_PROJECT_ARGS} --defaults --yes --verbose
	$(MAKE) example-setup EXAMPLE_DIR="$@"

docs/examples/mkdocs: INIT_PYTHON_PROJECT_ARGS+=--docs mkdocs
docs/examples/sphinx: INIT_PYTHON_PROJECT_ARGS+=--docs sphinx
docs/examples/minimal: INIT_PYTHON_PROJECT_ARGS+=--docs none --no-precommit --no-bumpversion
docs/examples/full: INIT_PYTHON_PROJECT_ARGS+=--docs mkdocs --precommit --bumpversion
docs/examples/gitlab: INIT_PYTHON_PROJECT_ARGS+=--docs mkdocs --precommit --bumpversion --remote gitlab
doc-examples: $(DOC_EXAMPLES)
$(DOC_EXAMPLES): uncopy-template copy-template
	@echo "Recreating '$@'..."
	@rm -rf "$@" && mkdir -p "$@"
	init-python-project "$@" --user-name jannismain ${INIT_PYTHON_PROJECT_ARGS} --defaults --yes --verbose
	@cd $@ &&\
		python -m venv .venv || echo "Couldn't setup virtual environment" &&\
		. .venv/bin/activate &&\
		pip install --upgrade pip &&\
		$(MAKE) install-dev || echo "Couldn't install dev environment for example"

example-setup: example-setup-commit example-setup-local
example-setup-commit:
	-cd ${EXAMPLE_DIR} &&\
		rm -rf .copier-answers.yml &&\
		git add . &&\
		git commit -m "automatic update" &&\
		git fetch &&\
		git branch --set-upstream-to=origin/main &&\
		git pull --rebase=True -X theirs
example-setup-local:
ifndef CI
	cd ${EXAMPLE_DIR} &&\
		python -m venv .venv || echo "Couldn't setup virtual environment" &&\
		source .venv/bin/activate &&\
		pip install --upgrade pip &&\
		$(MAKE) install-dev || echo "Couldn't install dev environment for example" &&\
		code --new-window .
endif

examples-clean: ## remove all published examples
	rm -rf $(PUBLISHED_EXAMPLES)

build/example:  ## build individual example for manual testing (will prompt for values!)
	rm -rf "$@"
	init-python-project "$@" ${INIT_PYTHON_PROJECT_ARGS}
	$(MAKE) example-setup EXAMPLE_DIR="$@"


.PHONY: docs docs-live docs-clean docs-clean-cache
MKDOCS_CMD?=build
MKDOCS_ARGS?=
docs: ## build documentation
docs: $(DOC_EXAMPLES)
	mkdocs $(MKDOCS_CMD) $(MKDOCS_ARGS)
docs-live: ## serve documentation locally
docs-live:
	$(MAKE) docs MKDOCS_CMD=serve MKDOCS_ARGS=--clean
docs-clean:
	rm -rf docs/examples public build/docs
docs-clean-cache:
	rm -rf build/.docs_cache


.PHONY: cspell cspell-ci
CSPELL_ARGS=--show-suggestions --show-context --config ".vscode/cspell.json" --unique
CSPELL_FILES="**/*.*"
DICT_FILE=.vscode/terms.txt
spellcheck: ## check spelling using cspell
	cspell ${CSPELL_ARGS} ${CSPELL_FILES}
spellcheck-ci:
	cspell --no-cache ${CSPELL_ARGS} ${CSPELL_FILES}
spellcheck-dump: ## save all flagged words to project terms dictionary
	cspell ${CSPELL_ARGS} ${CSPELL_FILES} --words-only >> ${DICT_FILE}
	sort --ignore-case --output=${DICT_FILE} ${DICT_FILE}


.PHONY: test
PYTEST_ARGS?=
test: ## run some tests
test: build-clean copy-template
	pytest ${PYTEST_ARGS} -m "not slow"
test-all: ## run all tests
test-all: build-clean copy-template
	pytest ${PYTEST_ARGS}


.PHONY: build install-build copy-template build-clean
PKGNAME=init_python_project
PKGDIR=src/${PKGNAME}
BUILDDIR?=build/dist
PYTHON?=python
TEMPLATE_SRC?=./template
TEMPLATE_DEST?=${PKGDIR}/template
build: build-clean copy-template ## build package
	@${PYTHON} -m pip install --upgrade build
	@${PYTHON} -m build --outdir ${BUILDDIR} .
install-build: build
	@pip uninstall -y ${PKGNAME}
	pip install --force-reinstall ${BUILDDIR}/*.whl
copy-template:
	@cp -r ${TEMPLATE_SRC} ${TEMPLATE_DEST}
	@cp copier.yaml ${PKGDIR}/.
uncopy-template:
	@rm -rf ${TEMPLATE_DEST} ${PKGDIR}/copier.yaml
link-template:
	@cd ${PKGDIR} &&\
		ln -s ../../${TEMPLATE_SRC} template &&\
		ln -s ../../copier.yaml copier.yaml
build-clean: uncopy-template ## remove build artifacts
	@rm -rf ${BUILDDIR}

.PHONY: release release-test release-tag release-pypi release-github
release: release-test release-tag build release-pypi release-github
release-test:
	@nox
release-tag:
	@git tag -m 'bump version to '`init-python-project --version` `init-python-project --version` --sign
release-pypi:
	twine upload ${BUILDDIR}/*
release-github:
	@git push --tags
	gh release create `init-python-project --version` \
		--title `init-python-project --version` \
		--notes '*[see changes](https://github.com/jannismain/python-project-template/blob/main/CHANGELOG.md#'`init-python-project --version | tr -d .`'---'`date -Idate`')*'
	gh release upload `init-python-project --version` ${BUILDDIR}/*.tar.gz ${BUILDDIR}/*.whl


.PHONY: help
# a nice way to document Makefiles, found here: https://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
