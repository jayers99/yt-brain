from yt_brain.application.cluster import _generate_slug


def test_generate_slug_without_api_key():
    """When api_key is empty, should generate numeric fallback slug."""
    titles = ["Video about Python", "Python Tutorial"]
    slug = _generate_slug(titles, set(), api_key="", fallback_index=1)
    assert slug == "cluster-01"


def test_generate_slug_without_api_key_deduplicates():
    """Numeric fallback should still deduplicate."""
    titles = ["Video about Python"]
    existing = {"cluster-01"}
    slug = _generate_slug(titles, existing, api_key="", fallback_index=1)
    assert slug == "cluster-01-2"
