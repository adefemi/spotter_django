from typing import Any, Dict, List, Tuple
import httpx


class OSRMClient:
    def __init__(self) -> None:
        self.base_url = "https://router.project-osrm.org"
        self._client = httpx.Client(base_url=self.base_url, timeout=20)

    def directions(self, coordinates: List[Tuple[float, float]], profile: str = "driving") -> Dict[str, Any]:
        # Input coordinates are (lat, lon). OSRM expects lon,lat, semicolon separated
        parts = [f"{lon},{lat}" for lat, lon in coordinates]
        coords = ";".join(parts)
        url = f"/route/v1/{profile}/{coords}"
        params = {
            "overview": "full",
            "geometries": "geojson",
            "steps": "true",
        }
        resp = self._client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, dict) or data.get("code") != "Ok":
            raise ValueError(f"OSRM error: {data}")
        # Normalize OSRM schema roughly to ORS-like
        routes = data.get("routes") or []
        if not routes:
            raise ValueError(f"OSRM no routes: {data}")
        route = routes[0]
        return {
            "routes": [
                {
                    "summary": {
                        "duration": route["duration"],
                        "distance": route["distance"],
                    },
                    "geometry": route["geometry"],
                    "segments": route.get("legs", []),
                }
            ]
        }


