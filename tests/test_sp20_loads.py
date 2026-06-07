from steel_frame_designer.sp20_loads import (
    LoadCaseValidationReport,
    LoadFactorReference,
    apply_load_factors,
    build_minimal_load_cases,
    load_sp20_load_cases_csv,
    validate_load_cases,
)


def test_minimal_load_cases_have_required_identity_fields() -> None:
    load_cases = build_minimal_load_cases(case_id="case_0001", tributary_width_m=6.0)

    report = validate_load_cases(load_cases, require_values=False, require_factors=False)

    assert isinstance(report, LoadCaseValidationReport)
    assert report.ok
    assert {case.load_id for case in load_cases} >= {
        "G_self_weight",
        "G_roof_dead",
        "S_symmetric",
        "S_left_unbalanced",
        "S_right_unbalanced",
        "W_plus_x",
        "W_minus_x",
        "Q_roof_maintenance",
    }
    assert all(case.direction for case in load_cases)
    assert all(case.unit for case in load_cases)
    assert all(case.source_norm for case in load_cases)


def test_template_csv_load_cases_report_missing_values_and_factors() -> None:
    load_cases = load_sp20_load_cases_csv("data/templates/sp20_loads.csv")

    report = validate_load_cases(load_cases)

    assert not report.ok
    issue_pairs = {(issue.load_id, issue.field) for issue in report.issues}
    assert ("G_roof_dead", "value") in issue_pairs
    assert ("G_roof_dead", "gamma_f") in issue_pairs
    assert ("S_symmetric", "value") in issue_pairs
    assert ("W_plus_x", "gamma_f") in issue_pairs


def test_load_factors_are_applied_from_external_table() -> None:
    load_cases = build_minimal_load_cases(case_id="case_0001", tributary_width_m=6.0)
    factor_table = [
        LoadFactorReference(
            load_id="S_symmetric",
            gamma_f=1.4,
            source_norm="SP 20.13330.2016",
            source_note="demo factor from test table",
        )
    ]

    updated_cases = apply_load_factors(load_cases, factor_table)
    snow_case = next(case for case in updated_cases if case.load_id == "S_symmetric")

    assert snow_case.gamma_f == 1.4
    assert snow_case.source_norm == "SP 20.13330.2016"
    assert "demo factor" in snow_case.notes


def test_validation_rejects_unsupported_unit() -> None:
    load_case = build_minimal_load_cases(case_id="case_0001", tributary_width_m=6.0)[1].model_copy(
        update={"unit": "tons"}
    )

    report = validate_load_cases([load_case], require_values=False, require_factors=False)

    assert not report.ok
    assert report.issues[0].code == "unsupported_unit"
