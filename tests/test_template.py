import itertools
import os
import tomllib
from pathlib import Path
from subprocess import check_call, check_output, run

import pytest
import yaml
from copier import run_copy
from pytest_venv import VirtualEnvironment

template = yaml.safe_load(Path(__file__).parent.with_name("copier.yaml").read_text())
SUPPORTED_REMOTES = template["remote"]["choices"].values()
SUPPORTED_DOCS = template["docs"]["choices"].values()
SUPPORTED_DOCS_TEMPLATES = ("none",)
SUPPORTED_DOCS_TEMPLATES_COMBINATIONS = [
    t
    for t in itertools.product(SUPPORTED_DOCS, SUPPORTED_DOCS_TEMPLATES)
    if t[1] == "none" or t[1].startswith(t[0])
]
"""All combinations of docs and docs_template options."""

fp_template = Path(__file__).parent.parent

required_static_data = dict(
    project_name="Sample Project",
    user_name="mkj",
)


def get_precommit_hooks(pre_commit_config_path: Path) -> list[str]:
    pre_commit_config = yaml.safe_load(pre_commit_config_path.open())
    return [hook["id"] for repo in pre_commit_config["repos"] for hook in repo["hooks"]]


@pytest.fixture
def venv(tmp_path):
    """Create virtual environment in subdirectory of tmp_path."""
    venv = VirtualEnvironment(tmp_path / ".venv")
    venv.create()
    (venv.path / ".gitignore").unlink()
    yield venv
    print(tmp_path)  # useful for debugging the built project


@pytest.mark.slow
@pytest.mark.parametrize("precommit", [True, False], ids=["pre-commit", "no pre-commit"])
@pytest.mark.parametrize(
    "docs,docs_template",
    SUPPORTED_DOCS_TEMPLATES_COMBINATIONS,
)
@pytest.mark.parametrize("remote", SUPPORTED_REMOTES)
def test_template_generation(
    venv: VirtualEnvironment,
    tmp_path: Path,
    precommit: bool,
    docs: str,
    docs_template: str,
    remote: str,
    project_name: str = "Sample Project",
):
    run_copy(
        str(fp_template),
        str(tmp_path),
        data=dict(
            **required_static_data,
            precommit=precommit,
            docs=docs,
            docs_template=docs_template,
            remote=remote,
        ),
        defaults=True,
        unsafe=True,
        vcs_ref="HEAD",
    )

    fp_readme = tmp_path / "README.md"
    assert fp_readme.is_file(), "new projects should have a README file"
    readme_content = fp_readme.read_text()
    assert readme_content.startswith(
        f"# {project_name}"
    ), "README should start with the project name"
    assert "## Installation" in readme_content, "README should have a getting started section"

    fp_changelog = tmp_path / "CHANGELOG.md"
    assert fp_changelog.is_file(), "new projects should have a CHANGELOG file"

    fp_precommit_config = tmp_path / ".pre-commit-config.yaml"
    assert fp_precommit_config.is_file() == precommit

    if precommit:
        # gitlabci-lint incompatible with sphinx, as ci job is imported from docs/.gitlab/docs.yml
        # so it is currently only included for projects using mkdocs with gitlab
        if remote.startswith("gitlab") and docs != "sphinx":
            assert "gitlabci-lint" in get_precommit_hooks(fp_precommit_config)
        else:
            assert "gitlabci-lint" not in get_precommit_hooks(fp_precommit_config)

    fp_git = tmp_path / ".git"
    assert fp_git.is_dir(), "new projects should be git repositories"

    fp_docs = tmp_path / "docs"
    if docs == "mkdocs":
        fp_mkdocs_cfg = tmp_path / "mkdocs.yml"
        assert fp_mkdocs_cfg.is_file(), "mkdocs configuration file should exist"
    elif docs == "sphinx":
        fp_sphinx_makefile = fp_docs / "Makefile"
        assert fp_sphinx_makefile.is_file(), "sphinx Makefile file should exist"
        fp_sphinx_requirements = fp_docs / "requirements.txt"
        assert fp_sphinx_requirements.is_file(), "sphinx requirements file should exist"
        fp_sphinx_ci_job = fp_docs / ".gitlab" / "docs.yml"
        assert fp_sphinx_ci_job.is_file(), "sphinx ci job should exist"

    use_docs = docs != "none"
    assert fp_docs.is_dir() == use_docs, "docs directory should exist if configured"

    fp_git_config = fp_git / "config"
    git_config = fp_git_config.read_text()
    assert (
        '[remote "origin"]' in git_config
    ), "new projects should have a remote repository configured"

    os.chdir(tmp_path)
    if docs_template != "none":
        # docs template needs to be formatted before we can assume
        # that all pre-commit hooks pass
        check_output(["git", "add", "."])
        run(["pre-commit", "run", "--all-files"])
    check_output(["git", "add", "."])
    check_output(["git", "commit", "-m", "initial commit"])

    # verify that example can be installed
    venv.install(".[dev,test]", editable=True)
    venv_bin = Path(venv.bin)

    # verify that pytest works and all tests pass
    check_output([venv_bin / "pytest", "-q"])


def test_default_branch_option(tmp_path: Path):
    default_branch = "custom"
    run_copy(
        str(fp_template),
        str(tmp_path),
        data=dict(
            project_name="Sample Project",
            user_name="mkj",
        ),
        unsafe=True,
        defaults=True,
        user_defaults={"default_branch": default_branch},
        vcs_ref="HEAD",
    )
    assert (
        check_output(["git", "status", "--branch", "--porcelain"], cwd=str(tmp_path))
        .decode()
        .split("\n")[0]  # first line -> branch info
        .split()[-1]  # last word -> branch
        == default_branch
    )


@pytest.mark.parametrize("remote", SUPPORTED_REMOTES)
def test_remote_option(tmp_path: Path, remote: str):
    user_name = "foo"
    project_name = "Wonderful Project"

    run_copy(
        str(fp_template),
        str(tmp_path),
        data=dict(
            project_name=project_name,
            remote=remote,
            user_name=user_name,
        ),
        unsafe=True,
        defaults=True,
        vcs_ref="HEAD",
    )

    git_remote_output = check_output(["git", "remote", "-v"], cwd=str(tmp_path)).decode()
    branch, remote_url, _ = git_remote_output.split("\n")[0].split()

    readme_template_url = (tmp_path / "README.md").open().readlines()[-1].strip()

    if remote == "github":
        assert remote_url == f"git@github.com:{user_name}/wonderful-project.git"
        assert (tmp_path / ".github").is_dir()
        assert "github.com" in readme_template_url
    if remote.startswith("gitlab"):
        gitlab_ci_yml = tmp_path / ".gitlab-ci.yml"
        assert gitlab_ci_yml.is_file()
        check_call(["pre-commit", "run", "--all-files", "gitlabci-lint"], cwd=str(tmp_path))


@pytest.mark.parametrize("docs", SUPPORTED_DOCS)
def test_docs_option(venv: VirtualEnvironment, tmp_path: Path, docs: str):
    root = tmp_path

    run_copy(
        str(fp_template),
        str(root),
        data=dict(
            **required_static_data,
            docs=docs,
        ),
        defaults=True,
        unsafe=True,
        vcs_ref="HEAD",
    )

    if docs == "mkdocs":
        fp_mkdocs_cfg = root / "mkdocs.yml"
        assert fp_mkdocs_cfg.is_file(), "mkdocs configuration file should exist"
    elif docs == "sphinx":
        fp_sphinx_makefile = root / "docs" / "Makefile"
        assert fp_sphinx_makefile.is_file(), "sphinx Makefile should exist"
        fp_sphinx_ci_job = root / "docs" / ".gitlab" / "docs.yml"
        assert fp_sphinx_ci_job.is_file(), "sphinx ci job should exist"

    if docs != "none":
        assert (root / "docs").is_dir(), "docs directory should exist"
        fp_requirements = root / "docs" / "requirements.txt"
        assert fp_requirements.is_file(), "doc requirements file should exist"

        # install example including its doc requirements
        venv.install(f"{root}", editable=True)
        for req in fp_requirements.open().readlines():
            if not req.strip().startswith("#"):
                venv.install(req)
        venv_bin = Path(venv.bin)

        # verify docs can be built
        fp_docs_built = tmp_path / "build" / "docs" / "html"
        assert not fp_docs_built.is_dir()
        check_output(
            ["make", "docs"],
            env={
                "SPHINXBUILD": str(venv_bin / "sphinx-build"),
                "MKDOCS_BIN": str(venv_bin / "mkdocs"),
            },
            cwd=tmp_path,
        )
        assert fp_docs_built.is_dir(), "docs should have been built into build directory"
        assert (fp_docs_built / "index.html").is_file(), "index should exist"


@pytest.mark.parametrize("docs", SUPPORTED_DOCS)
@pytest.mark.parametrize("remote", SUPPORTED_REMOTES)
def test_publish_docs_ci(tmp_path: Path, docs: str, remote: str):
    root = tmp_path

    run_copy(
        str(fp_template),
        str(root),
        data=dict(
            **required_static_data,
            docs=docs,
            remote=remote,
        ),
        defaults=True,
        unsafe=True,
        vcs_ref="HEAD",
    )

    ci_platform = "gitlab" if remote.startswith("gitlab") else remote
    docs_job = "docs"

    if ci_platform == "gitlab":
        ci_file = root / ".gitlab-ci.yml"
        if docs == "sphinx":
            # job for sphinx is included via separate file due to external template support
            ci_file = root / "docs" / ".gitlab" / "docs.yml"
    elif ci_platform == "github":
        ci_file = root / ".github" / "workflows" / "ci.yaml"

    assert ci_file.is_file()
    ci_config = yaml.safe_load(ci_file.read_text())

    if ci_platform == "github":
        ci_config = ci_config["jobs"]

    match (docs, ci_platform):
        case ("none", _):
            assert docs_job not in ci_config, "docs job should not be present if docs are disabled"
        case _:
            assert docs_job in ci_config, "docs job should be present if docs are enabled"


DOCS_WITH_TEMPLATE = [c for c in SUPPORTED_DOCS_TEMPLATES_COMBINATIONS if c[1] != "none"]
"""Only those combinations that actually use a template."""


@pytest.mark.parametrize("docs,docs_template", DOCS_WITH_TEMPLATE)
def test_docs_with_template(tmp_path: Path, docs: str, docs_template: str):
    root = tmp_path

    run_copy(
        str(fp_template),
        str(root),
        data=dict(
            **required_static_data,
            docs=docs,
            docs_template=docs_template,
        ),
        defaults=True,
        unsafe=True,
        vcs_ref="HEAD",
    )

    docs = root / "docs"

    docs_requirements = docs / "requirements.txt"
    assert docs_requirements.is_file(), "all doc templates must come with a requirements file"

    ci_job = docs / ".gitlab" / "docs.yml"
    assert ci_job.is_file(), "doc templates must provide their ci job in separate file"


def read_pyproject_version(path: Path):
    return tomllib.load(path.open("rb"))["project"]["version"]


def read_last_commit_msg(cwd: Path | str = None):
    return check_output(["git", "log", "-1", "--pretty=%B"], cwd=str(cwd or ".")).decode().strip()


@pytest.mark.parametrize("bumpversion", [True, False], ids=["bumpversion", "no-bumpversion"])
def test_bumpversion_option(venv: VirtualEnvironment, tmp_path: Path, bumpversion: bool):
    run_copy(
        str(fp_template),
        str(tmp_path),
        data=dict(
            **required_static_data,
            bumpversion=bumpversion,
            precommit=False,  # makes testing easier
        ),
        unsafe=True,
        defaults=True,
        vcs_ref="HEAD",
    )
    if not bumpversion:
        assert not (tmp_path / ".bumpversion.cfg").is_file()
        return

    assert (tmp_path / ".bumpversion.cfg").is_file()
    fp_pyproject = tmp_path / "pyproject.toml"

    os.chdir(tmp_path)
    check_output(["git", "add", "."])
    check_output(["git", "commit", "-m", "initial commit"])

    venv.install(".[dev]", editable=True)
    venv_bin = Path(venv.bin)

    # verify that pytest works and all tests pass
    check_output([venv_bin / "bumpversion", "-h"])

    # bumpversion git interaction requires initial commit
    run(["git", "add", "."])
    run(["git", "commit", "-m", "initial commit", "--no-verify"])
    assert read_pyproject_version(fp_pyproject) == "0.0.1"
    check_call([venv_bin / "bumpversion", "patch"])
    assert read_pyproject_version(fp_pyproject) == "0.0.2"
    assert read_last_commit_msg() == "bump v0.0.1 -> v0.0.2"
    check_call([venv_bin / "bumpversion", "minor"])
    assert read_pyproject_version(fp_pyproject) == "0.1.0"
    assert read_last_commit_msg() == "bump v0.0.2 -> v0.1.0"
    check_output([venv_bin / "bumpversion", "major"])
    assert read_pyproject_version(fp_pyproject) == "1.0.0"
    assert read_last_commit_msg() == "bump v0.1.0 -> v1.0.0"
