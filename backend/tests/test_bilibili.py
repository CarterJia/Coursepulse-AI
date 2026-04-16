from unittest.mock import patch, MagicMock

from app.services.bilibili import search_videos


def _mock_response(results: list[dict], code: int = 0) -> MagicMock:
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {
        "code": code,
        "data": {"result": results},
    }
    return resp


def _make_result(
    bvid: str = "BV1test",
    title: str = "测试视频",
    description: str = "这是一个测试",
    duration: str = "5:30",
    play: int = 50000,
    author: str = "TestUP",
    pic: str = "//cover.jpg",
) -> dict:
    return {
        "bvid": bvid,
        "title": title,
        "description": description,
        "duration": duration,
        "play": play,
        "author": author,
        "pic": pic,
    }


def _mock_session(response: MagicMock | Exception) -> MagicMock:
    session = MagicMock()
    if isinstance(response, Exception):
        session.get.side_effect = response
    else:
        session.get.return_value = response
    return session


@patch("app.services.bilibili.time.sleep", lambda _s: None)
@patch("app.services.bilibili._get_session")
def test_search_videos_returns_filtered_results(mock_get_session):
    mock_get_session.return_value = _mock_session(_mock_response([
        _make_result(bvid="BV1", duration="5:30", play=50000),
        _make_result(bvid="BV2", duration="15:00", play=80000),  # too long
        _make_result(bvid="BV3", duration="3:00", play=500),     # too few plays
        _make_result(bvid="BV4", duration="8:00", play=20000),
    ]))
    results = search_videos("蒙特卡洛树搜索 讲解")
    bvids = [v.bvid for v in results]
    assert "BV1" in bvids
    assert "BV4" in bvids
    assert "BV2" not in bvids
    assert "BV3" not in bvids


@patch("app.services.bilibili.time.sleep", lambda _s: None)
@patch("app.services.bilibili._get_session")
def test_search_videos_parses_duration_correctly(mock_get_session):
    mock_get_session.return_value = _mock_session(_mock_response([
        _make_result(bvid="BV1", duration="9:59", play=20000),
        _make_result(bvid="BV2", duration="10:00", play=20000),
        _make_result(bvid="BV3", duration="1:02:00", play=20000),
    ]))
    results = search_videos("test")
    assert len(results) == 1
    assert results[0].bvid == "BV1"
    assert results[0].duration_seconds == 599


@patch("app.services.bilibili.time.sleep", lambda _s: None)
@patch("app.services.bilibili._get_session")
def test_search_videos_returns_empty_on_api_error(mock_get_session):
    mock_get_session.return_value = _mock_session(Exception("network error"))
    results = search_videos("test")
    assert results == []


@patch("app.services.bilibili.time.sleep", lambda _s: None)
@patch("app.services.bilibili._get_session")
def test_search_videos_returns_empty_on_bad_code(mock_get_session):
    mock_get_session.return_value = _mock_session(_mock_response([], code=-1))
    results = search_videos("test")
    assert results == []


@patch("app.services.bilibili.time.sleep", lambda _s: None)
@patch("app.services.bilibili._get_session")
def test_search_videos_strips_html_from_title(mock_get_session):
    mock_get_session.return_value = _mock_session(_mock_response([
        _make_result(
            bvid="BV1",
            title='<em class="keyword">蒙特卡洛</em>树搜索讲解',
            play=50000,
            duration="5:00",
        ),
    ]))
    results = search_videos("蒙特卡洛")
    assert results[0].title == "蒙特卡洛树搜索讲解"
