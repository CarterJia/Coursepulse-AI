import os

from app.services.reporting import _strip_missing_images


DOC_ID = "d6e5a8f4-0000-0000-0000-000000000001"


def _url(doc_id: str, filename: str) -> str:
    return f"/api/files/{doc_id}/{filename}"


def test_keeps_image_that_exists_on_disk(tmp_path):
    derived_dir = tmp_path / "derived" / DOC_ID
    derived_dir.mkdir(parents=True)
    (derived_dir / "page_3_img_0.png").write_bytes(b"\x89PNG")
    body = f"Look: ![caption]({_url(DOC_ID, 'page_3_img_0.png')}) end."

    result = _strip_missing_images(body, DOC_ID, str(tmp_path))

    assert result == body  # unchanged


def test_strips_image_whose_file_is_missing(tmp_path):
    (tmp_path / "derived" / DOC_ID).mkdir(parents=True)  # dir exists, file doesn't
    body = f"Before ![x]({_url(DOC_ID, 'page_7_img_0.png')}) after."

    result = _strip_missing_images(body, DOC_ID, str(tmp_path))

    assert "page_7_img_0.png" not in result
    assert "Before  after." in result  # image ref removed, surrounding text kept


def test_strips_image_referencing_a_different_document(tmp_path):
    other_doc = "00000000-0000-0000-0000-00000000aaaa"
    other_dir = tmp_path / "derived" / other_doc
    other_dir.mkdir(parents=True)
    (other_dir / "page_1_img_0.png").write_bytes(b"")
    body = f"Cross ![]({_url(other_doc, 'page_1_img_0.png')}) doc."

    result = _strip_missing_images(body, DOC_ID, str(tmp_path))

    # the file physically exists, but not under OUR doc_id → strip anyway
    assert "page_1_img_0.png" not in result


def test_passes_through_body_with_no_image_refs(tmp_path):
    body = "# 纯文字段落\n\n一些解释, 没有图片。"

    result = _strip_missing_images(body, DOC_ID, str(tmp_path))

    assert result == body


def test_handles_multiple_refs_independently(tmp_path):
    derived_dir = tmp_path / "derived" / DOC_ID
    derived_dir.mkdir(parents=True)
    (derived_dir / "real.png").write_bytes(b"")
    body = (
        f"A ![]({_url(DOC_ID, 'real.png')}) "
        f"B ![]({_url(DOC_ID, 'ghost.png')}) C"
    )

    result = _strip_missing_images(body, DOC_ID, str(tmp_path))

    assert "real.png" in result
    assert "ghost.png" not in result
