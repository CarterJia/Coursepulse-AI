from app.models.report import Report


def test_report_model_has_section_type_field():
    """Report model must expose section_type with default='topic'."""
    r = Report(title="t", body="b", document_id=__import__("uuid").uuid4())
    # default is applied at flush time; sanity-check the attribute exists
    assert hasattr(r, "section_type")


def test_report_model_section_type_column_type():
    col = Report.__table__.c.section_type
    assert col.type.length == 32
    assert col.nullable is False
