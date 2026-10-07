from pathlib import Path

import pexpect
import pytest


@pytest.fixture
def bin():
    import os

    yield Path(os.getenv("BIN_PATH", "."))


@pytest.mark.slow
def test_template_generation_via_cli(bin: Path, tmp_path: Path):
    child = pexpect.spawn(str(bin / "init-python-project"), ["my-project"], cwd=tmp_path, timeout=3)
    child.expect(".* project.*")
    child.sendline("My Project")
    child.expect(".* package.*")
    child.sendline("")  # accept default
    child.expect(".* pre-commit.*")
    child.send("y")
    child.expect(".* bumpversion.*")
    child.send("y")
    child.expect(".* documentation.*")
    child.sendline("")  # accept default
    child.expect(".* platform.*")
    child.sendline("")  # accept default
    child.expect(".* name.*")
    child.sendline("cool-user")
    child.expect(".*mail.*")
    child.sendline("cool-user@example.com")
    child.expect(".* remote.*")
    child.sendline("")  # accept default
    child.expect(".* initial git branch.*")
    child.sendline("")  # accept default
