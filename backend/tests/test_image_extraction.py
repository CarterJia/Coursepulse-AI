from pathlib import Path
import fitz

from app.services.image_extraction import extract_images


def _make_pdf_with_image(tmp_path: Path) -> Path:
    """Create a minimal PDF with 2 pages, 1 embedded PNG on page 2."""
    doc = fitz.open()
    # page 1 - text only
    page1 = doc.new_page()
    page1.insert_text((72, 72), "Page 1 text only")
    # page 2 - text + embedded PNG
    page2 = doc.new_page()
    page2.insert_text((72, 72), "Page 2 with image")
    # minimal 1x1 red PNG
    png_bytes = bytes.fromhex(
        "89504E470D0A1A0A0000000D49484452000000010000000108020000"
        "00907753DE0000000C4944415478DA63F8CFC0000003010100F70341"
        "430000000049454E44AE426082"
    )
    page2.insert_image(fitz.Rect(100, 100, 150, 150), stream=png_bytes)
    out_path = tmp_path / "sample_with_images.pdf"
    doc.save(str(out_path))
    doc.close()
    return out_path


def test_extract_images_returns_manifest(tmp_path):
    pdf_path = _make_pdf_with_image(tmp_path)
    out_dir = tmp_path / "derived"

    manifest = extract_images(str(pdf_path), str(out_dir))

    # manifest maps page_number -> list of relative filenames
    assert manifest == {2: ["page_2_img_0.png"]}
    assert (out_dir / "page_2_img_0.png").exists()
    assert (out_dir / "page_2_img_0.png").stat().st_size > 0


def test_extract_images_empty_pdf(tmp_path):
    doc = fitz.open()
    doc.new_page().insert_text((72, 72), "only text")
    pdf_path = tmp_path / "no_img.pdf"
    doc.save(str(pdf_path))
    doc.close()

    manifest = extract_images(str(pdf_path), str(tmp_path / "out"))
    assert manifest == {}
