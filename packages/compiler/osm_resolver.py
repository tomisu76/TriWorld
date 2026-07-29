"""OSM resolver: fetch OSM data via Overpass API with cache and retry/backoff.

Supports multiple Overpass endpoints with mirror rotation.
Caches responses locally with SHA-256 verification.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any

import httpx
from lxml import etree

from packages.compiler.osm_parser import parse_osm
from packages.contracts.road_ir import RoadNetworkIR


# Default Overpass endpoints (mirrors for redundancy)
DEFAULT_OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.tekuminal.dev/api/interpreter",
    "https://overpass-api.de/api/interpreter",
]


@dataclass
class OsmSource:
    """Configuration for an OSM data source."""

    name: str
    endpoint: str
    license: str = "ODbL-1.0"
    timeout: float = 60.0


@dataclass
class OsmFetchResult:
    """Result of an OSM fetch operation."""

    data: bytes
    source: OsmSource
    url: str
    sha256: str
    fetch_time: float
    element_count: int
    bounds: Tuple[float, float, float, float]


class OsmResolver:
    """Fetch OSM data via Overpass API with cache and retry/backoff."""

    def __init__(
        self,
        cache_dir: Path,
        endpoints: Optional[List[str]] = None,
        max_retries: int = 5,
        backoff_base: float = 2.0,
        timeout: float = 60.0,
    ):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.endpoints = endpoints or DEFAULT_OVERPASS_ENDPOINTS
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self.timeout = timeout
        self._client: Optional[httpx.Client] = None
        self._endpoint_index = 0

    @property
    def client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(timeout=self.timeout, follow_redirects=True)
        return self._client

    def _cache_path(self, query_hash: str) -> Path:
        """Return the cache path for a query hash."""
        return self.cache_dir / "osm" / query_hash[:2] / f"{query_hash}.osm"

    def _hash_path(self, query_hash: str) -> Path:
        """Return the hash file path for a query."""
        return self._cache_path(query_hash).with_suffix(".sha256")

    def _compute_hash(self, data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    def _compute_query_hash(self, bbox: Tuple[float, float, float, float], query: str) -> str:
        """Compute a deterministic hash for a query."""
        content = f"{bbox}|{query}"
        return hashlib.sha256(content.encode()).hexdigest()

    def is_cached(self, query_hash: str) -> bool:
        """Check if a query result is cached and valid."""
        cache_path = self._cache_path(query_hash)
        hash_path = self._hash_path(query_hash)
        if not cache_path.exists() or not hash_path.exists():
            return False
        expected_hash = hash_path.read_text().strip()
        actual_hash = self._compute_hash(cache_path.read_bytes())
        return expected_hash == actual_hash

    def _next_endpoint(self) -> str:
        """Get the next endpoint in rotation (round-robin)."""
        endpoint = self.endpoints[self._endpoint_index]
        self._endpoint_index = (self._endpoint_index + 1) % len(self.endpoints)
        return endpoint

    def _build_bbox_query(self, bbox: Tuple[float, float, float, float]) -> str:
        """Build an Overpass QL query for a bounding box."""
        min_lon, min_lat, max_lon, max_lat = bbox
        return f"""
        [out:xml][timeout:60];
        (
          way["highway"](around:{max(max_lon - min_lon, max_lat - min_lat) * 111000}, {min_lat}, {min_lon}, {max_lat}, {max_lon});
          node(w);
        );
        out body;
        """.strip()

    def _fetch_with_retry(
        self,
        endpoint: str,
        query: str,
        bbox: Tuple[float, float, float, float],
    ) -> Tuple[bytes, str]:
        """Fetch data from a single endpoint with retry and backoff."""
        url = f"{endpoint}?data={httpx.QueryParams({'Q': query}).encode()}"
        # Use POST for large queries
        last_error: Optional[Exception] = None

        for attempt in range(self.max_retries):
            try:
                # Try GET first, fall back to POST
                if len(query) < 2000:
                    response = self.client.get(endpoint, params={"data": query})
                else:
                    response = self.client.post(endpoint, data={"data": query})

                response.raise_for_status()
                return response.content, str(response.url)
            except (httpx.HTTPError, httpx.RequestError) as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    delay = self.backoff_base * (2 ** attempt)
                    time.sleep(delay)

        raise RuntimeError(f"Failed to fetch from {endpoint}: {last_error}")

    def _count_elements(self, data: bytes) -> int:
        """Count OSM elements in XML data."""
        try:
            root = etree.fromstring(data)
            return len(root.findall(".//way")) + len(root.findall(".//node"))
        except etree.XMLSyntaxError:
            return 0

    def _extract_bounds(self, data: bytes) -> Tuple[float, float, float, float]:
        """Extract bounds from OSM XML data."""
        try:
            root = etree.fromstring(data)
            bounds_elem = root.find(".//bounds")
            if bounds_elem is not None:
                min_lat = float(bounds_elem.get("minlat", 0))
                min_lon = float(bounds_elem.get("minlon", 0))
                max_lat = float(bounds_elem.get("maxlat", 0))
                max_lon = float(bounds_elem.get("maxlon", 0))
                return (min_lon, min_lat, max_lon, max_lat)
        except (etree.XMLSyntaxError, ValueError):
            pass
        return (0.0, 0.0, 0.0, 0.0)

    def fetch_bbox(
        self,
        bbox: Tuple[float, float, float, float],
        query: Optional[str] = None,
    ) -> OsmFetchResult:
        """Fetch OSM data for a bounding box.

        Args:
            bbox: (min_lon, min_lat, max_lon, max_lat)
            query: Optional custom Overpass QL query. If None, uses default bbox query.

        Returns:
            OsmFetchResult with data and metadata
        """
        if query is None:
            query = self._build_bbox_query(bbox)

        query_hash = self._compute_query_hash(bbox, query)

        # Check cache first
        if self.is_cached(query_hash):
            cache_path = self._cache_path(query_hash)
            data = cache_path.read_bytes()
            source = OsmSource(name="cache", endpoint="local")
            return OsmFetchResult(
                data=data,
                source=source,
                url=f"cache:{query_hash}",
                sha256=self._compute_hash(data),
                fetch_time=time.time(),
                element_count=self._count_elements(data),
                bounds=self._extract_bounds(data),
            )

        # Try each endpoint with rotation
        last_error: Optional[Exception] = None
        for attempt in range(self.max_retries * len(self.endpoints)):
            endpoint = self._next_endpoint()
            source = OsmSource(name=f"overpass-{attempt % len(self.endpoints)}", endpoint=endpoint)

            try:
                start_time = time.time()
                data, url = self._fetch_with_retry(endpoint, query, bbox)
                fetch_time = time.time() - start_time

                # Cache the result
                cache_path = self._cache_path(query_hash)
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                cache_path.write_bytes(data)
                hash_path = self._hash_path(query_hash)
                hash_path.write_text(self._compute_hash(data))

                return OsmFetchResult(
                    data=data,
                    source=source,
                    url=url,
                    sha256=self._compute_hash(data),
                    fetch_time=fetch_time,
                    element_count=self._count_elements(data),
                    bounds=self._extract_bounds(data),
                )
            except Exception as e:
                last_error = e
                if attempt < self.max_retries * len(self.endpoints) - 1:
                    delay = self.backoff_base * (2 ** (attempt // len(self.endpoints)))
                    time.sleep(delay)

        raise RuntimeError(f"Failed to fetch OSM data after all retries: {last_error}")

    def fetch_bbox_as_network(
        self,
        bbox: Tuple[float, float, float, float],
        query: Optional[str] = None,
    ) -> Tuple[RoadNetworkIR, OsmFetchResult]:
        """Fetch OSM data and parse it into a RoadNetworkIR.

        Args:
            bbox: (min_lon, min_lat, max_lon, max_lat)
            query: Optional custom Overpass QL query

        Returns:
            (RoadNetworkIR, OsmFetchResult)
        """
        result = self.fetch_bbox(bbox, query)

        # Parse the OSM XML
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".osm", delete=False) as f:
            f.write(result.data)
            temp_path = f.name

        try:
            network = parse_osm(temp_path)
        finally:
            Path(temp_path).unlink(missing_ok=True)

        return network, result

    def close(self):
        """Close the HTTP client."""
        if self._client is not None:
            self._client.close()
            self._client = None


def parse_overpass_json(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Parse an Overpass API JSON response into a list of element dicts.

    Args:
        data: Parsed JSON from Overpass API (dict with 'elements' key)

    Returns:
        List of element dictionaries, each with at least 'type', 'id',
        and 'tags' keys.
    """
    elements = data.get("elements", [])
    result = []
    for elem in elements:
        parsed = {
            "type": elem.get("type", "unknown"),
            "id": elem.get("id", 0),
            "lat": elem.get("lat"),
            "lon": elem.get("lon"),
            "tags": elem.get("tags", {}),
        }
        if "nodes" in elem:
            parsed["nodes"] = elem["nodes"]
        if "center" in elem:
            parsed["center"] = elem["center"]
        result.append(parsed)
    return result
