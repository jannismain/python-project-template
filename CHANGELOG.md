# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [unreleased]

### Added

- documentation of a known issue with `NoConsoleScreenBufferError` during runtime under Windows git-bash (provided by [@lieutdan13])
- email address in pyproject.toml is now configurable (provided by to [@lieutdan13])
- remove non-public Gitlab remotes (replace `gitlab-iis` and `gitlab-fhg` with public `gitlab`)
- remove non-public doc templates (remove `sphinx-fhg-iis` template)

## [0.0.6] - 2023-10-12

### Added

- automatically assign `asprunner` tag in GitLab CI configuration intended for `gitlab-fhg` remote.
- GitLab CI artifacts are set to expire after 1 week to reduce overall storage usage (most recent artifact is kept)
- pre-commit hook that lints `.gitlab-ci.yml` and prevents committing a faulty config
    - available for projects with gitlab remote using mkdocs

### Changed

- replace sphinx-autodoc2 with sphinx-autoapi for better google-style docstring support

### Fixed

- Gitlab projects using mkdocs didn't install doc requirements during CI
- docstring argument section not parsed correctly

## [0.0.5] - 2023-09-25

### Fixed

- badge image url for projects hosted on GitLab

## [0.0.4] - 2023-09-25

### Changed

- rename `use_precommit` and `use_bumpversion` options to simply `precommit` and `bumpversion`

### Fixed

- doc template: all templates files are included now
- do not include doc requirements in `make install-dev` if no docs are configured
- documentation examples are now built using the cli

## [0.0.3] - 2023-09-21

### Added

- github ci now runs tests, collects coverage and creates maintainability and coverage badges
- add [sphinx_template](https://git01.iis.fhg.de/sch/sphinx_template/) as an option when choosing sphinx for documentation

### Changed

- template now uses a static documentation badge provided by shields.io

### Fixed

- link to pipeline in README now correctly links to github actions
- when bumpversion is selected, add `bump2version` to dev dependencies

## [0.0.2] - 2023-09-19

### Added

- `init-python-project --version` outputs template version

## [0.0.1] - 2023-09-18

Started this template by forking [pypa/sampleproject] and converting it to a copier template.

An example project (comparable to [pypa/sampleproject]) can be found at [jannismain/python-project-template-example].

### Added

- CHANGELOG proposal from [jimustafa](https://github.com/jimustafa) in [!185](https://github.com/pypa/sampleproject/pull/185)
- added `__main__` and `cli` modules (based on discussion of [!67](https://github.com/pypa/sampleproject/pull/67))
- Refactored into copier template
    - add option to use `bumpversion`
    - add option to use `pre-commit`
    - add option to choose between documentation tools: `MkDocs` or `Sphinx`
    - add `remote` option ('github' (default), 'gitlab-fhg', 'gitlab-iis')
        - if `gitlab-*` is selected, Gitlab CI configuration is added
        - if `github` is selected, GitHub actions are added
    - add Gitlab CI configuration to
        - run tests
        - collect test coverage and publish it as [Gitlab report artefact](https://docs.gitlab.com/ee/ci/yaml/artifacts_reports.html#artifactsreportscoverage_report)
        - calculate maintainability metric
        - generate badges that are shown in the README
        - generate documentation and publish via [Gitlab Pages](https://docs.gitlab.com/ee/user/project/pages/)
    - add Github Actions configuration to
        - generate documentation and publish via [Github Pages](https://pages.github.com/)
    - add default branch option (default: `main`)
- Documentation
    - add user, reference and developer guides
- `init_python_project` Package
    - contains template + `init-python-project` command line interface

### Changed

- convert to a copier template
- tests are executed using pytest (was unittest)

### Removed

- trove classifiers (only relevant when publishing to PyPI)

[unreleased]: https://github.com/jannismain/python-project-template/compare/v0.0.6...HEAD
[0.0.6]: https://github.com/jannismain/python-project-template/compare/0.0.5...0.0.6
[0.0.5]: https://github.com/jannismain/python-project-template/compare/0.0.4...0.0.5
[0.0.4]: https://github.com/jannismain/python-project-template/compare/0.0.3...0.0.4
[0.0.3]: https://github.com/jannismain/python-project-template/compare/0.0.2...0.0.3
[0.0.2]: https://github.com/jannismain/python-project-template/compare/0.0.1...0.0.2
[0.0.1]: https://github.com/jannismain/python-project-template/releases/tag/0.0.1
[pypa/sampleproject]: https://github.com/pypa/sampleproject
[jannismain/python-project-template-example]: https://github.com/jannismain/python-project-template-example

[@lieutdan13]: https://github.com/lieutdan13
