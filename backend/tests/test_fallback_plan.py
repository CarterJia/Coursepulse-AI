from app.services.report_planner import build_fallback_plan, validate_plan


def test_fallback_plan_groups_every_4_pages():
    pages = [{"page_number": i, "text": f"p{i}"} for i in range(1, 11)]
    plan = build_fallback_plan(pages)

    # 10 pages / 4 = 3 topics (1-4, 5-8, 9-10)
    assert len(plan["topics"]) == 3
    assert plan["topics"][0]["source_pages"] == [1, 2, 3, 4]
    assert plan["topics"][2]["source_pages"] == [9, 10]
    # produced plan must pass validator
    validate_plan(plan, max_page=10)


def test_fallback_plan_single_page():
    pages = [{"page_number": 1, "text": "only"}]
    plan = build_fallback_plan(pages)
    assert len(plan["topics"]) == 1
    assert plan["topics"][0]["source_pages"] == [1]
    validate_plan(plan, max_page=1)
