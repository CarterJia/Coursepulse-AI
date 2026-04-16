from pathlib import Path
import fitz
from PIL import Image
import io

from app.services.image_extraction import extract_images


def _png_bytes(width: int, height: int, color=(255, 0, 0)) -> bytes:
    img = Image.new("RGB", (width, height), color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _make_pdf_with_image(
    tmp_path: Path, img_width: int = 400, img_height: int = 300
) -> Path:
    """Create a minimal PDF with 2 pages, 1 embedded PNG on page 2."""
    doc = fitz.open()
    # page 1 - text only
    page1 = doc.new_page()
    page1.insert_text((72, 72), "Page 1 text only")
    # page 2 - text + embedded PNG (content-sized, passes A-filter)
    page2 = doc.new_page()
    page2.insert_text((72, 72), "Page 2 with image")
    page2.insert_image(
        fitz.Rect(100, 100, 400, 400), stream=_png_bytes(img_width, img_height)
    )
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


def test_extract_images_filters_tiny_icons(tmp_path):
    """A-filter: a 50x50 image is too small to be real content — drop it."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_image(fitz.Rect(10, 10, 40, 40), stream=_png_bytes(50, 50))
    pdf_path = tmp_path / "tiny.pdf"
    doc.save(str(pdf_path))
    doc.close()

    manifest = extract_images(str(pdf_path), str(tmp_path / "out"))
    assert manifest == {}


def test_extract_images_filters_repeating_logo(tmp_path):
    """B-filter: the same image on every page is a header/footer/logo — drop it."""
    logo_bytes = _png_bytes(300, 300, color=(0, 128, 255))
    doc = fitz.open()
    for _ in range(5):
        page = doc.new_page()
        page.insert_image(fitz.Rect(10, 10, 310, 310), stream=logo_bytes)
    pdf_path = tmp_path / "logo_every_page.pdf"
    doc.save(str(pdf_path))
    doc.close()

    manifest = extract_images(str(pdf_path), str(tmp_path / "out"))
    assert manifest == {}


def test_extract_images_empty_pdf(tmp_path):
    doc = fitz.open()
    doc.new_page().insert_text((72, 72), "only text")
    pdf_path = tmp_path / "no_img.pdf"
    doc.save(str(pdf_path))
    doc.close()

    manifest = extract_images(str(pdf_path), str(tmp_path / "out"))
    assert manifest == {}
