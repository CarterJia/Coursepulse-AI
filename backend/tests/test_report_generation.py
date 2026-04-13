from app.services.reporting import build_report_prompt


def test_build_report_prompt_includes_context_chunks():
    chunks = [{"page_number": 2, "text": "Gradient descent updates weights by moving opposite the gradient."}]
    prompt = build_report_prompt("Explain gradient descent", chunks)
    assert "Explain gradient descent" in prompt
    assert "opposite the gradient" in prompt
