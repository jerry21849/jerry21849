"""Unified subprocess runner for local CLI tools (onchainos, twitter, etc.).

Every call returns (stdout, stderr, returncode). When the CLI is not found,
returns (None, error_msg, -1) so callers can degrade gracefully.
"""

import shutil
import subprocess
import json
from collections.abc import Sequence


def find_cli(name: str) -> str | None:
    """Return full path to *name* CLI, or None if not on PATH."""
    return shutil.which(name)


def run_cli(
    cmd: Sequence[str],
    timeout: int = 30,
) -> tuple[str | None, str | None, int]:
    """Execute *cmd*, return (stdout, stderr, returncode).

    On CLI-not-found, return (None, error_msg, -1).
    On timeout, return (partial_stdout, error_msg, -1).
    """
    if not cmd:
        return None, "Empty command", -1
    cli = find_cli(cmd[0])
    if not cli:
        return None, f"CLI '{cmd[0]}' not found on PATH", -1

    proc = subprocess.Popen(
        [cli, *cmd[1:]],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
        return stdout, stderr, proc.returncode
    except subprocess.TimeoutExpired:
        proc.kill()
        partial, stderr = proc.communicate()
        return partial, f"Timeout after {timeout}s: {stderr}", -1


def run_cli_json(
    cmd: Sequence[str],
    timeout: int = 30,
) -> dict | list | None:
    """Run a CLI command and parse its stdout as JSON.

    Returns parsed JSON on success, None on any failure.
    """
    stdout, stderr, rc = run_cli(cmd, timeout=timeout)
    if rc != 0 or not stdout:
        return None
    try:
        return json.loads(stdout.strip())
    except json.JSONDecodeError:
        return None
