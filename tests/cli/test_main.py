"""Tests for CLI main commands.

Author:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

import subprocess
import sys

from typer.testing import CliRunner

from backend.cli.main import app


def test_cli_main_help() -> None:
    """Test CLI main module help command."""
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0


def test_cli_main_name_main() -> None:
    """Test CLI main module when run as __main__."""
    # Run the module as __main__ to trigger line 54
    result = subprocess.run([sys.executable, "-m", "backend.cli.main", "--help"], capture_output=True, text=True)
    assert result.returncode == 0


def test_cli_main_list_command() -> None:
    """Test list command."""
    runner = CliRunner()
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "Not implemented" in result.stdout


def test_cli_main_add_command() -> None:
    """Test add command."""
    runner = CliRunner()
    result = runner.invoke(app, ["add", "Test task"])
    assert result.exit_code == 0
    assert "Not implemented" in result.stdout


def test_cli_main_chat_command() -> None:
    """Test chat command."""
    runner = CliRunner()
    result = runner.invoke(app, ["chat"])
    assert result.exit_code == 0
    assert "Not implemented" in result.stdout
