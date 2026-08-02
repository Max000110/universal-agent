import pytest
from typer.testing import CliRunner
from antigravity_cli.platform import PlatformEnvironment
from antigravity_cli.cli import app

runner = CliRunner()


def test_platform_environment():
    summary = PlatformEnvironment.get_system_summary()
    assert "platform" in summary
    assert "terminal_width" in summary
    assert summary["terminal_width"] >= 40


def test_cli_version_command():
    res = runner.invoke(app, ["version"])
    assert res.exit_code == 0
    assert "universal-agent version" in res.stdout


def test_cli_status_command(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    res = runner.invoke(app, ["status"])
    assert res.exit_code == 0
    assert "Antigravity Status" in res.stdout
    assert "CHATGPT" in res.stdout


def test_cli_exec_command(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    res = runner.invoke(app, ["exec", "/status"])
    assert res.exit_code == 0
    assert "System Status" in res.stdout or "Antigravity Status" in res.stdout
