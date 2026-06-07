"""Command-line interface skeleton."""

from __future__ import annotations

import typer

app = typer.Typer(help="Steel Frame Designer CLI.")


@app.command()
def init() -> None:
    """Initialize a project workspace."""
    typer.echo("Project initialization is not implemented yet.")


@app.command("validate-input")
def validate_input() -> None:
    """Validate input configuration and CSV templates."""
    typer.echo("Input validation is not implemented yet.")


@app.command("build-loads")
def build_loads() -> None:
    """Build SP 20 load cases."""
    typer.echo("Load generation is not implemented yet.")


@app.command("import-lira")
def import_lira() -> None:
    """Import LIRA exports."""
    typer.echo("LIRA import is not implemented yet.")


@app.command("build-dataset")
def build_dataset() -> None:
    """Build ML dataset."""
    typer.echo("Dataset build is not implemented yet.")


@app.command()
def train() -> None:
    """Train baseline model."""
    typer.echo("Training is not implemented yet.")


@app.command()
def predict() -> None:
    """Predict top-N sections."""
    typer.echo("Prediction is not implemented yet.")


@app.command()
def verify() -> None:
    """Verify candidate sections."""
    typer.echo("Verification is not implemented yet.")


@app.command()
def report() -> None:
    """Generate report."""
    typer.echo("Report generation is not implemented yet.")


@app.command()
def ui() -> None:
    """Run Streamlit UI."""
    typer.echo("Streamlit UI is not implemented yet.")


if __name__ == "__main__":
    app()
