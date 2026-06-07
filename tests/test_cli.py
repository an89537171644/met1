from typer.testing import CliRunner

from steel_frame_designer.cli import app


def test_cli_help() -> None:
    result = CliRunner().invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "Steel Frame Designer CLI" in result.output


def test_cli_doctor() -> None:
    result = CliRunner().invoke(app, ["doctor"])

    assert result.exit_code == 0
    assert "Project:" in result.output
    assert "Roof slope:" in result.output


def test_cli_validate_input_reports_warnings() -> None:
    result = CliRunner().invoke(app, ["validate-input"])

    assert result.exit_code == 0
    assert "Input configuration schema is valid." in result.output
    assert "WARNING:" in result.output


def test_cli_report_accepts_path_argument(tmp_path) -> None:
    report_path = tmp_path / "report.md"

    result = CliRunner().invoke(app, ["report", str(report_path)])

    assert result.exit_code == 0
    assert report_path.exists()
