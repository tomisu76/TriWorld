"""Tests for OSM resolver: bbox queries, caching, retry/backoff."""

import tempfile
import pytest
from pathlib import Path

from packages.compiler.osm_resolver import (
    OsmResolver,
    OsmSource,
    OsmFetchResult,
    DEFAULT_OVERPASS_ENDPOINTS,
    parse_overpass_json,
)


class TestOsmResolver:
    def test_resolver_init(self):
        """Test OsmResolver initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            resolver = OsmResolver(cache_dir=Path(tmpdir))
            assert resolver.cache_dir == Path(tmpdir)
            assert resolver.max_retries == 5
            assert len(resolver.endpoints) > 0
            resolver.close()

    def test_resolver_cache_path(self):
        """Test cache path computation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            resolver = OsmResolver(cache_dir=Path(tmpdir))
            query_hash = "abc123def456"
            path = resolver._cache_path(query_hash)
            assert path.suffix == ".osm"
            assert "abc" in str(path)
            assert "123def456.osm" in str(path)
            resolver.close()

    def test_resolver_cache_miss(self):
        """Test cache miss detection."""
        with tempfile.TemporaryDirectory() as tmpdir:
            resolver = OsmResolver(cache_dir=Path(tmpdir))
            query_hash = "nonexistent_hash"
            assert not resolver.is_cached(query_hash)
            resolver.close()

    def test_resolver_cache_hit(self):
        """Test cache hit after writing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            resolver = OsmResolver(cache_dir=Path(tmpdir))
            query_hash = "test_hash"
            cache_path = resolver._cache_path(query_hash)
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            test_data = b'<?xml version="1.0"?><osm></osm>'
            cache_path.write_bytes(test_data)
            hash_path = resolver._hash_path(query_hash)
            hash_path.write_text(resolver._compute_hash(test_data))
            assert resolver.is_cached(query_hash)
            resolver.close()

    def test_resolver_cache_corrupted(self):
        """Test corrupted cache detection."""
        with tempfile.TemporaryDirectory() as tmpdir:
            resolver = OsmResolver(cache_dir=Path(tmpdir))
            query_hash = "test_hash"
            cache_path = resolver._cache_path(query_hash)
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_bytes(b'<?xml version="1.0"?><osm></osm>')
            hash_path = resolver._hash_path(query_hash)
            hash_path.write_text("wrong_hash")
            assert not resolver.is_cached(query_hash)
            resolver.close()

    def test_resolver_hash_computation(self):
        """Test SHA-256 hash computation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            resolver = OsmResolver(cache_dir=Path(tmpdir))
            data = b"test osm data"
            h = resolver._compute_hash(data)
            assert len(h) == 64
            resolver.close()

    def test_resolver_query_hash_deterministic(self):
        """Test that query hash is deterministic."""
        with tempfile.TemporaryDirectory() as tmpdir:
            resolver = OsmResolver(cache_dir=Path(tmpdir))
            bbox = (2.34, 48.84, 2.36, 48.86)
            query = "[out:xml];"
            h1 = resolver._compute_query_hash(bbox, query)
            h2 = resolver._compute_query_hash(bbox, query)
            assert h1 == h2
            resolver.close()

    def test_resolver_build_bbox_query(self):
        """Test bbox query construction."""
        with tempfile.TemporaryDirectory() as tmpdir:
            resolver = OsmResolver(cache_dir=Path(tmpdir))
            bbox = (2.34, 48.84, 2.36, 48.86)
            query = resolver._build_bbox_query(bbox)
            assert "out:xml" in query
            assert "2.34" in query
            assert "48.84" in query
            resolver.close()

    def test_resolver_endpoint_rotation(self):
        """Test endpoint round-robin rotation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            resolver = OsmResolver(cache_dir=Path(tmpdir))
            endpoints = resolver.endpoints
            first = resolver._next_endpoint()
            second = resolver._next_endpoint()
            assert first == endpoints[0]
            assert second == endpoints[1]
            resolver.close()

    def test_resolver_count_elements(self):
        """Test element counting in OSM XML."""
        with tempfile.TemporaryDirectory() as tmpdir:
            resolver = OsmResolver(cache_dir=Path(tmpdir))
            xml = b'<?xml version="1.0"?><osm><node id="1"/><node id="2"/><way id="1"/></osm>'
            count = resolver._count_elements(xml)
            assert count == 3
            resolver.close()

    def test_resolver_extract_bounds(self):
        """Test bounds extraction from OSM XML."""
        with tempfile.TemporaryDirectory() as tmpdir:
            resolver = OsmResolver(cache_dir=Path(tmpdir))
            xml = b'<?xml version="1.0"?><osm><bounds minlat="48.84" minlon="2.34" maxlat="48.86" maxlon="2.36"/></osm>'
            bounds = resolver._extract_bounds(xml)
            assert bounds == (2.34, 48.84, 2.36, 48.86)
            resolver.close()


class TestParseOverpassJson:
    def test_parse_empty(self):
        """Test parsing empty Overpass response."""
        data = {"elements": []}
        result = parse_overpass_json(data)
        assert len(result) == 0

    def test_parse_with_nodes(self):
        """Test parsing Overpass response with nodes."""
        data = {
            "elements": [
                {"type": "node", "id": 1, "lat": 48.85, "lon": 2.35, "tags": {"name": "Test"}},
                {"type": "node", "id": 2, "lat": 48.86, "lon": 2.36, "tags": {"highway": "traffic_signals"}},
            ]
        }
        result = parse_overpass_json(data)
        assert len(result) == 2
        assert result[0]["id"] == 1
        assert result[0]["type"] == "node"

    def test_parse_with_ways(self):
        """Test parsing Overpass response with ways."""
        data = {
            "elements": [
                {"type": "way", "id": 100, "nodes": [1, 2, 3], "tags": {"highway": "primary"}},
            ]
        }
        result = parse_overpass_json(data)
        assert len(result) == 1
        assert result[0]["type"] == "way"
        assert result[0]["id"] == 100
