from typing import Tuple
import httpx


class NominatimGeocoder:
    def __init__(self) -> None:
        self.base_url = "https://nominatim.openstreetmap.org"
        self._client = httpx.Client(base_url=self.base_url, timeout=20, headers={
            "User-Agent": "spotter-app/1.0 (contact: dev@example.com)",
        })

    def geocode(self, query: str) -> Tuple[float, float]:
        resp = self._client.get("/search", params={
            "q": query,
            "format": "json",
            "limit": 1,
        })
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, list) or not data:
            raise ValueError(f"Nominatim no result for '{query}'")
        first = data[0]
        lat = float(first["lat"])  # type: ignore[index]
        lon = float(first["lon"])  # type: ignore[index]
        return (lat, lon)


