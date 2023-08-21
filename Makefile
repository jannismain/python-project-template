USER_NAME?=jannismain
REMOTE?=github
REMOTE_URL?=git@github.com:jannismain/python-project-template-example.git

# These targets are used to push examples to all supported remotes
examples: example-github example-gitlab-fhg example-gitlab-iis
example-github: example-clean-github example example-setup
example-gitlab-fhg: example-clean-gitlab-fhg
	$(MAKE) example USER_NAME=mkj REMOTE=gitlab-fhg REMOTE_URL=git@gitlab.cc-asp.fraunhofer.de:mkj/sample-project.git
	$(MAKE) example-setup REMOTE=gitlab-fhg
example-gitlab-iis: example-clean-gitlab-iis
	$(MAKE) example USER_NAME=mkj REMOTE=gitlab-iis REMOTE_URL=git@git01.iis.fhg.de:mkj/sample-project.git
	$(MAKE) example-setup REMOTE=gitlab-iis

# This target can be used for ad-hoc manual testing
example-manual: example-clean-manual
	copier copy ${COPIER_ARGS} -d "project_name=Sample Project" -d "package_name=sample_project" -d "user_name=mkj" . ./build/example_manual
	$(MAKE) example-setup EXAMPLE_DIR=./build/example_manual

COPIER_ARGS?=--trust
COPIER_DEFAULT_VALUES?=-d "project_name=Sample Project" -d "package_name=sample_project" --defaults
EXAMPLE_DIR?=./build/example_$(subst -,_,$(REMOTE))
example:
	copier copy ${COPIER_ARGS} ${COPIER_DEFAULT_VALUES} -d "user_name=${USER_NAME}" -d "remote=${REMOTE}" -d "remote_url=${REMOTE_URL}" . ${EXAMPLE_DIR}

example-setup:
	-cd ${EXAMPLE_DIR} &&\
		rm -rf .copier-answers.yml &&\
		git add . &&\
		git commit -m "automatic update" &&\
		git fetch &&\
		git branch --set-upstream-to=origin/main &&\
		git pull --rebase=True -X theirs
	$(MAKE) example-setup-local REMOTE=${REMOTE}
example-setup-local:
ifndef CI
	cd ${EXAMPLE_DIR} &&\
		pyenv local project-template-example || echo "Couldn't set example env via pyenv" &&\
		pip install --upgrade pip &&\
		$(MAKE) install-dev || echo "Couldn't install dev environment for example" &&\
		code --new-window .
endif

examples-clean: example-clean-github example-clean-gitlab-fhg example-clean-gitlab-iis
example-clean-github:
	rm -rf build/example_github && mkdir -p build/example_github
example-clean-gitlab-fhg:
	rm -rf build/example_gitlab_fhg && mkdir -p build/example_gitlab_fhg
example-clean-gitlab-iis:
	rm -rf build/example_gitlab_iis && mkdir -p build/example_gitlab_iis
example-clean-manual:
	rm -rf build/example_manual && mkdir -p build/example_manual

.PHONY: docs docs-live docs-clean docs-clean-cache
MKDOCS_CMD?=build
MKDOCS_ARGS?=
docs: docs/examples/mkdocs docs/examples/sphinx docs/examples/default
	mkdocs $(MKDOCS_CMD) $(MKDOCS_ARGS)
docs-live:
	$(MAKE) docs MKDOCS_CMD=serve
docs/examples/mkdocs:
	copier copy ${COPIER_ARGS} ${COPIER_DEFAULT_VALUES} -d "user_name=mkj" -d "docs=mkdocs" . docs/examples/mkdocs
docs/examples/sphinx:
	copier copy ${COPIER_ARGS} ${COPIER_DEFAULT_VALUES} -d "user_name=mkj" -d "docs=sphinx" . docs/examples/sphinx
docs/examples/default:
	copier copy ${COPIER_ARGS} ${COPIER_DEFAULT_VALUES} -d "user_name=mkj" . docs/examples/default
docs-clean:
	rm -rf docs/examples public
docs-clean-cache:
	rm -rf build/.docs_cache

.PHONY: cspell cspell-ci
CSPELL_ARGS=--show-suggestions --show-context --config ".vscode/cspell.json" --unique
CSPELL_FILES="**/*.*"
DICT_FILE=.vscode/terms.txt
cspell: ## check spelling using cspell
	cspell ${CSPELL_ARGS} ${CSPELL_FILES}
cspell-ci:
	cspell --no-cache ${CSPELL_ARGS} ${CSPELL_FILES}
cspell-dump:
	cspell ${CSPELL_ARGS} ${CSPELL_FILES} --words-only >> ${DICT_FILE}
	sort --ignore-case -s --output=${DICT_FILE} ${DICT_FILE}

.PHONY: test
PYTEST_ARGS=-n auto
test:
	pytest ${PYTEST_ARGS} -m "not slow"
test-all:
	pytest ${PYTEST_ARGS}
