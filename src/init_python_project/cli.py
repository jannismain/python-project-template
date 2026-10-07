import logging
import sys
from enum import StrEnum
from pathlib import Path
from subprocess import check_output
from typing import Annotated, Optional

import typer
from copier import run_copy
from typer import Argument, Option, Typer, colors, confirm, style

app = Typer()

__version__ = "0.0.6"


def version_callback(value: bool) -> None:
    if value:
        print(__version__)
        sys.exit(0)


class DocumentationTool(StrEnum):
    "which documentation tool to use"
    mkdocs = "mkdocs"
    sphinx = "sphinx"
    none = "none"


class DocumentationTemplate(StrEnum):
    "which documentation template to use"
    builtin = "none"


class RemotePlatform(StrEnum):
    "which remote platform to configure"
    github = "github"
    gitlab = "gitlab"


def CustomOptional(_type=bool, help="", custom_flag: str | list = None, **kwargs):
    if issubclass(_type, StrEnum):
        kwargs = {"case_sensitive": False, **kwargs}
        if not help:
            help = _type.__doc__

    kwargs = {"show_default": False, "help": help, **kwargs}

    if custom_flag is None:
        return Annotated[Optional[_type], Option(**kwargs)]

    if isinstance(custom_flag, str):
        custom_flag = [custom_flag]
    return Annotated[Optional[_type], Option(*custom_flag, **kwargs)]


@app.command(name="init-python-project")
def cli(
    # data passed to the underlying copier template
    target_path: Path = Argument("new-project"),
    project_name: CustomOptional(str, "project name (title case with spaces)") = None,
    package_name: CustomOptional(str, "Python package name (lowercase with underscores)") = None,
    user_name: CustomOptional(str, "your user name") = None,
    email_address: CustomOptional(str, "your email address") = None,
    docs: CustomOptional(DocumentationTool) = None,
    docs_template: CustomOptional(DocumentationTemplate) = None,
    remote: CustomOptional(RemotePlatform) = None,
    remote_url: CustomOptional(str, "ssh url where your repository will be hosted on") = None,
    precommit: CustomOptional(bool, "include pre-commit hooks") = None,
    bumpversion: CustomOptional(bool, "include bumpversion configuration") = None,
    # arguments that affect project creation
    defaults: Annotated[
        bool, Option("--defaults", "-d", help="automatically accept all default options")
    ] = False,
    dry_run: Annotated[bool, Option("--dry-run", help="do not actually create project")] = False,
    always_confirm: Annotated[
        bool, Option("--yes", "-y", help="answer any confirmation request with yes")
    ] = False,
    version: Annotated[
        Optional[bool],
        Option("--version", callback=version_callback, is_eager=True, help="show version and exit"),
    ] = None,
    verbose: Annotated[
        Optional[bool],
        typer.Option(
            "--verbose",
            "-v",
            callback=lambda x: logging.basicConfig(
                level=logging.INFO if x else logging.WARN, format="%(message)s"
            ),
            is_eager=True,
            help="show more information",
        ),
    ] = False,
    copier_args: Annotated[
        Optional[list[str]],
        typer.Option("--copier-arg", help="anything you want to pass to copier"),
    ] = None,
) -> None:
    """Executes the CLI command to create a new project.

    For a list of supported copier arguments, see
    https://copier.readthedocs.io/en/stable/reference/main/#copier.main.Worker.

    Note that `src_path`, `dest_path`, `vcs_ref`, `data`, `defaults`, `user_defaults` and `unsafe`
    are already set by this command. Further, `--dry-run` corresponds to copier's `--pretend` and
    `--yes` implies copier's `--overwrite`.
    """

    if docs_template not in [None, "none"] and (
        docs is None or (docs is not None and not docs_template.value.startswith(docs.value))
    ):
        typer.secho(
            f"Error: selected template ({docs_template}) not compatible "
            f"with documentation tool ({docs})",
            fg=colors.RED,
            err=True,
        )
        raise typer.Exit(1)

    # cast enums to their values
    for option in "docs remote".split():
        if locals()[option] is not None:
            locals()[option] = locals()[option].value

    # assemble values provided by the user
    data = {}
    for (
        option
    ) in "project_name package_name user_name email_address docs remote remote_url precommit bumpversion".split():
        value = locals()[option]
        if value is not None:
            logging.info("%s: %s", option, value)
            data[option] = value

    if (
        target_path.is_dir()
        and any(target_path.iterdir())
        and not always_confirm
        and not confirm(
            style(
                f"Target directory '{target_path}' is not empty! Continue?",
                fg=colors.YELLOW,
            )
        )
    ):
        sys.exit(1)

    # parse copier args
    copier_args = {
        k.replace("--", "").replace("-", "_"): v
        for k, v in (
            arg.split("=") if "=" in arg else arg.split() if " " in arg else (arg, True)
            for arg in (copier_args or [])
        )
    }

    run_copy(
        src_path=str(Path(__file__).parent.absolute()),
        dst_path=target_path,
        unsafe=True,
        data=data,
        user_defaults=dict(
            user_name=check_output(["whoami"]).decode().strip() if user_name is None else user_name,
            project_name=target_path.name.replace("-", " ").replace("_", " ").title(),
            email_address=email_address,
        ),
        defaults=defaults,
        overwrite=always_confirm,
        pretend=dry_run or copier_args.pop("pretend", False),
        quiet=True,
        **copier_args,
    )


if __name__ == "__main__":
    app()
