import http.client
import urllib.error
from unittest.mock import MagicMock, patch

import pytest

from inat import (
    FAMILIES,
    FAMILY_NAMES,
    InatAPIError,
    _fetch_batch,
    _observation_queues,
    fetch_json,
    get_next_observation,
    get_photo_url,
    get_species_name,
    load_question,
)


def test_families_have_required_keys():
    for _name, info in FAMILIES.items():
        assert "common" in info
        assert "taxon_id" in info
        assert isinstance(info["taxon_id"], int)


def test_family_names_matches_families():
    assert FAMILY_NAMES == list(FAMILIES.keys())


def test_get_photo_url_replaces_size():
    obs = {"photos": [{"url": "https://example.com/photos/square.jpg"}]}
    assert get_photo_url(obs) == "https://example.com/photos/medium.jpg"
    assert get_photo_url(obs, size="large") == "https://example.com/photos/large.jpg"


def test_get_photo_url_no_photos():
    assert get_photo_url({}) is None
    assert get_photo_url({"photos": []}) is None


def test_get_species_name_with_common():
    obs = {"taxon": {"preferred_common_name": "Daisy", "name": "Bellis perennis"}}
    assert get_species_name(obs) == "Daisy (Bellis perennis)"


def test_get_species_name_without_common():
    obs = {"taxon": {"name": "Bellis perennis"}}
    assert get_species_name(obs) == "Bellis perennis"


def test_get_species_name_empty():
    assert get_species_name({}) == "Unknown"


def test_load_question_returns_expected_keys():
    fake_obs = {
        "photos": [{"url": "https://example.com/square.jpg", "attribution": "CC BY Someone"}],
        "taxon": {"preferred_common_name": "Daisy", "name": "Bellis perennis"},
        "uri": "https://inaturalist.org/observations/1",
    }
    with patch("inat.get_next_observation", return_value=fake_obs):
        q = load_question()
    assert q is not None
    assert q["family"] in FAMILY_NAMES
    assert "photo_url" in q
    assert "species" in q
    assert "attribution" in q


def test_load_question_returns_none_on_no_obs():
    with patch("inat.get_next_observation", return_value=None):
        assert load_question() is None


def test_load_question_returns_none_on_no_photo():
    fake_obs = {"photos": [], "taxon": {"name": "Test"}, "uri": ""}
    with patch("inat.get_next_observation", return_value=fake_obs):
        assert load_question() is None


def test_fetch_json():
    mock_response = MagicMock()
    mock_response.read.return_value = b'{"results": [1, 2, 3]}'
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = MagicMock(return_value=False)

    with patch("inat.urllib.request.urlopen", return_value=mock_response):
        data = fetch_json("https://example.com/api")
    assert data == {"results": [1, 2, 3]}


def test_fetch_batch():
    fake_response = {"results": [{"id": 1}, {"id": 2}, {"id": 3}]}
    with patch("inat.fetch_json", return_value=fake_response):
        results = _fetch_batch(12345)
    assert len(results) == 3
    assert all(isinstance(r, dict) for r in results)


def test_fetch_batch_empty():
    with patch("inat.fetch_json", return_value={"results": []}):
        results = _fetch_batch(12345)
    assert results == []


def test_get_next_observation_uses_queue():
    family = "Rosaceae"
    fake_obs = {"id": 42}
    _observation_queues[family] = [fake_obs]
    try:
        result = get_next_observation(family)
        assert result == fake_obs
        assert _observation_queues[family] == []
    finally:
        _observation_queues.pop(family, None)


def test_get_next_observation_refills_empty_queue():
    family = "Rosaceae"
    _observation_queues.pop(family, None)
    fake_obs = [{"id": 1}, {"id": 2}]
    with patch("inat._fetch_batch", return_value=list(fake_obs)):
        result = get_next_observation(family)
    assert result is not None
    _observation_queues.pop(family, None)


def test_get_next_observation_returns_none_when_api_empty():
    family = "Rosaceae"
    _observation_queues.pop(family, None)
    with patch("inat._fetch_batch", return_value=[]):
        result = get_next_observation(family)
    assert result is None
    _observation_queues.pop(family, None)


def test_fetch_json_raises_inat_api_error_on_http_error():
    error = urllib.error.HTTPError(
        url="https://example.com", code=503, msg="Service Unavailable",
        hdrs=http.client.HTTPMessage(), fp=None,
    )
    with patch("inat.urllib.request.urlopen", side_effect=error):
        with pytest.raises(InatAPIError):
            fetch_json("https://example.com")


def test_fetch_json_raises_inat_api_error_on_url_error():
    error = urllib.error.URLError(reason="Name or service not known")
    with patch("inat.urllib.request.urlopen", side_effect=error):
        with pytest.raises(InatAPIError):
            fetch_json("https://example.com")
