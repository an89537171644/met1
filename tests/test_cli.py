from typer.testing import CliRunner

from steel_frame_designer.cli import app


def test_cli_help() -> None:
    result = CliRunner().invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "Steel Frame Designer CLI" in result.output
