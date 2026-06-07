from steel_frame_designer.lira_import import LiraImportRecord, validate_lira_element_forces


def test_template_lira_forces_report_has_blank_cell_issues() -> None:
    report = validate_lira_element_forces("data/templates/lira_element_forces.csv")

    assert report.row_count == 1
    assert not report.ok
    assert any(issue.code == "blank_cell" and issue.column == "N_kN" for issue in report.issues)


def test_lira_import_record_parses_success_flag() -> None:
    record = LiraImportRecord(case_id="case_0001", lira_model_file="model.lir", success="true")

    assert record.success is True
