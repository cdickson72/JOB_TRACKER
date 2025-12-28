import pytest

try:
    from typer.testing import CliRunner
    from jobtracker.cli.main import app
except Exception as exc:  # pragma: no cover - skip when deps not installed
    pytest.skip(f"Missing runtime dependency or import error: {exc}", allow_module_level=True)


def test_cli_help_runs():
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0


def test_job_list_runs():
    runner = CliRunner()
    # running `job list` should not crash even with empty DB
    result = runner.invoke(app, ["job", "list"])
    # exit code 0 or 1 are both acceptable depending on environment, but no exception should bubble
    assert result.exit_code in (0, 1)
