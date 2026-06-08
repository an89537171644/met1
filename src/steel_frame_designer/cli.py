"""Command-line interface."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from .config import ensure_project_dirs, load_config, validate_config, validation_warnings
from .demo import run_demo as execute_demo
from .lira_import import import_lira_forces, validate_lira_element_forces
from .reports import write_markdown_report
from .sp20_loads import build_minimal_load_cases

app = typer.Typer(help="Steel Frame Designer CLI.")


@app.command()
def init(config: Path = Path("config.example.yaml")) -> None:
    """Initialize a project workspace."""
    cfg = load_config(config)
    ensure_project_dirs(cfg)
    typer.echo("Project directories are ready.")


@app.command("doctor")
def doctor(config: Path = Path("config.example.yaml")) -> None:
    """Print a short project health summary."""
    cfg = load_config(config)
    typer.echo(f"Project: {cfg.project.name}")
    typer.echo(f"Frame: {cfg.frame.geometry.span_m:g} m span")
    typer.echo(f"Roof slope: {cfg.frame.geometry.computed_roof_slope_deg:.2f} deg")
    typer.echo(f"SP16: {cfg.project.norms.steel_design}")
    typer.echo(f"SP20: {cfg.project.norms.loads}")
    warnings = validation_warnings(cfg)
    typer.echo(f"Warnings: {len(warnings)}")


@app.command("validate-input")
def validate_input(config: Path = Path("config.example.yaml")) -> None:
    """Validate input configuration and CSV templates."""
    cfg = load_config(config)
    report = validate_config(cfg)
    typer.echo("Input configuration schema is valid.")
    for issue in report.issues:
        typer.echo(f"{issue.severity.value.upper()}: {issue.path}: {issue.message}")
    if report.errors:
        raise typer.Exit(1)


@app.command("build-loads")
def build_loads(config: Path = Path("config.example.yaml")) -> None:
    """Build SP 20 load cases."""
    cfg = load_config(config)
    cases = build_minimal_load_cases(
        case_id=cfg.project.project_id,
        tributary_width_m=cfg.frame.geometry.frame_spacing_m,
    )
    for case in cases:
        typer.echo(f"{case.load_id}: {case.group.value} {case.scheme} [{case.unit}]")


@app.command("import-lira")
def import_lira(path: Path) -> None:
    """Import LIRA exports."""
    rows = import_lira_forces(path)
    report = validate_lira_element_forces(path)
    typer.echo(f"Imported LIRA force rows: {len(rows)}")
    typer.echo(f"Validation issues: {len(report.issues)}")


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


@app.command("run-demo")
def run_demo(
    frame_case: Annotated[
        Path,
        typer.Option(help="Demo frame YAML file."),
    ] = Path("data/samples/frame_case.yaml"),
    sample_root: Annotated[
        Path,
        typer.Option(help="Directory with demo CSV samples."),
    ] = Path("data/samples"),
    output_root: Annotated[
        Path,
        typer.Option(help="Directory where demo outputs are written."),
    ] = Path("."),
) -> None:
    """Run the full demo pipeline."""
    result = execute_demo(frame_case=frame_case, sample_root=sample_root, output_root=output_root)
    for step in result.steps:
        typer.echo(f"{step}: ok")
    typer.echo(f"Selected section: {result.selected_section_id}")
    for path in result.output_files:
        typer.echo(f"Generated: {path}")


@app.command()
def report(
    path: Annotated[Path, typer.Argument(help="Markdown report path.")] = Path("reports/report.md"),
) -> None:
    """Generate report."""
    write_markdown_report(path, "Steel Frame Designer Report", ["MVP placeholder report."])
    typer.echo(f"Report written: {path}")


@app.command()
def ui() -> None:
    """Run Streamlit UI."""
    typer.echo("Run Streamlit later with: streamlit run src/steel_frame_designer/ui_streamlit.py")


if __name__ == "__main__":
    app()
