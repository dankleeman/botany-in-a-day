import json
import random
import time
import urllib.error
import urllib.request

from config import config
from families import FAMILIES, FAMILY_NAMES

API_BASE = "https://api.inaturalist.org/v1"

# Per-family queue of pre-fetched observations
_observation_queues: dict[str, list[dict]] = {}

_RETRYABLE_STATUS = {429, 500, 502, 503, 504}
_MAX_RETRIES = 4
_BACKOFF_BASE = 1.0  # seconds


class InatAPIError(Exception):
    pass


def fetch_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "BotanyQuiz/1.0"})
    last_exc: Exception | None = None
    for attempt in range(_MAX_RETRIES):
        if attempt:
            time.sleep(_BACKOFF_BASE * (2 ** (attempt - 1)))
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            last_exc = e
            if e.code not in _RETRYABLE_STATUS:
                raise InatAPIError(f"iNaturalist error {e.code}: {e.reason}") from e
        except urllib.error.URLError as e:
            last_exc = e
    raise InatAPIError(
        f"iNaturalist unavailable after {_MAX_RETRIES} attempts: {last_exc}"
    ) from last_exc


def _fetch_batch(taxon_id: int) -> list[dict]:
    """Fetch a batch of research-grade observations, shuffled."""
    url = (
        f"{API_BASE}/observations"
        f"?taxon_id={taxon_id}"
        f"&photos=true"
        f"&quality_grade=research"
        f"&place_id={config.place_id}"
        + ("&term_id=12&term_value_id=13" if config.flowering_only else "")
        + f"&photo_license=cc0,cc-by,cc-by-sa"
        f"&per_page={config.batch_size}"
        f"&order_by=random"
    )
    data = fetch_json(url)
    results = data.get("results", [])
    random.shuffle(results)
    return results


def get_next_observation(family: str) -> dict | None:
    """Pop the next observation for a family, refilling the queue if empty."""
    taxon_id = int(FAMILIES[family]["taxon_id"])
    queue = _observation_queues.get(family, [])
    if not queue:
        queue = _fetch_batch(taxon_id)
        _observation_queues[family] = queue
    if not queue:
        return None
    return queue.pop()


def get_photo_url(observation: dict, size: str = "medium") -> str | None:
    if not observation.get("photos"):
        return None
    url = observation["photos"][0]["url"]
    return url.replace("/square.", f"/{size}.")


def get_species_name(observation: dict) -> str:
    taxon = observation.get("taxon", {})
    common = taxon.get("preferred_common_name", "")
    scientific = taxon.get("name", "Unknown")
    if common:
        return f"{common} ({scientific})"
    return scientific


def load_question(active_families: list[str] | None = None):
    """Pick a random family and get the next observation from its queue."""
    choices = active_families or FAMILY_NAMES
    family = random.choice(choices)
    info = FAMILIES[family]
    obs = get_next_observation(family)
    if not obs:
        return None
    photo_url = get_photo_url(obs, size="medium")
    if not photo_url:
        return None
    species = get_species_name(obs)
    photo_attribution = obs.get("photos", [{}])[0].get("attribution", "")
    obs_url = obs.get("uri", "")
    return {
        "family": family,
        "common": info["common"],
        "photo_url": photo_url,
        "species": species,
        "attribution": photo_attribution,
        "obs_url": obs_url,
    }
