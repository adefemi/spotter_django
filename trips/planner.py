from datetime import datetime
from typing import Any, Dict, List, Tuple

from .osrm_client import OSRMClient
from .nominatim import NominatimGeocoder
from .hos import HOSPlanner, DutySegment
from .geometry import cumulative_distances, interpolate_point


def plan_trip(
    current_location: str,
    pickup_location: str,
    dropoff_location: str,
    cycle_hours_used: float,
    start_time: datetime,
) -> Dict[str, Any]:
    geocoder = NominatimGeocoder()
    cur = geocoder.geocode(current_location)
    pick = geocoder.geocode(pickup_location)
    drop = geocoder.geocode(dropoff_location)
    osrm = OSRMClient()
    directions = osrm.directions([cur, pick, drop], profile="driving")

    # Sum duration hours and distance miles from ORS
    summary = directions["routes"][0]["summary"]
    duration_hours = summary["duration"] / 3600.0
    distance_miles = summary["distance"] / 1609.34

    # Simple drive segmentation: treat total duration as single driving block
    hos = HOSPlanner(start_time=start_time, cycle_hours_used=cycle_hours_used)
    hos.add_pickup()
    # Insert fuel stops roughly every 1000 miles, 0.5h each
    fuel_interval_miles = 1000.0
    fuel_count = int(distance_miles // fuel_interval_miles)
    if fuel_count <= 0:
        hos.drive(duration_hours)
    else:
        # Evenly split total driving time into fuel_count+1 segments
        segment_hours = duration_hours / (fuel_count + 1)
        for i in range(fuel_count + 1):
            hos.drive(segment_hours)
            if i < fuel_count:
                hos.add_fuel_stop()
    hos.add_dropoff()

    # Build ELD day segments payload
    eld_days: List[Dict[str, Any]] = []
    by_date: Dict[str, List[DutySegment]] = {}
    for seg in hos.segments:
        key = seg.start.strftime("%Y-%m-%d")
        by_date.setdefault(key, []).append(seg)
    for day, segments in by_date.items():
        eld_days.append({
            "date": day,
            "segments": [
                {
                    "start": s.start.isoformat(),
                    "end": s.end.isoformat(),
                    "status": s.status,
                    "note": s.note,
                }
                for s in segments
            ],
        })

    # Return geometry and steps
    route_obj = directions["routes"][0]
    route_geo = route_obj.get("geometry") if isinstance(route_obj, dict) else None
    steps = route_obj.get("segments") or route_obj.get("legs") or []

    # Build stops with ETAs and approximate coordinates
    coords_lonlat = route_geo.get("coordinates", [])  # [lon, lat]
    coords_latlon = [(lat, lon) for lon, lat in coords_lonlat]
    cumdist = cumulative_distances(coords_latlon) if coords_latlon else []
    stops = []
    # pickup at start
    if coords_latlon:
        stops.append({
            "type": "pickup",
            "eta": hos.segments[0].start.isoformat(),
            "lat": coords_latlon[0][0],
            "lon": coords_latlon[0][1],
            "duration_hours": 1.0,
        })
    # iterate segments to capture breaks/rests/fuel and estimate positions by distance fraction of total
    total_miles = cumdist[-1] if cumdist else distance_miles
    driven_so_far = 0.0
    for seg in hos.segments:
        if seg.status in ("OFF", "ON") and seg.note:
            # off-duty or on-duty non-driving stop
            if seg.note.startswith("30-min break") or seg.note.startswith("10-hr rest") or seg.note.startswith("Fueling"):
                frac = min(max(driven_so_far / total_miles, 0.0), 1.0) if total_miles > 0 else 0.0
                target = frac * total_miles
                lat, lon = (None, None)
                if cumdist:
                    lat, lon = interpolate_point(coords_latlon, cumdist, target)
                stops.append({
                    "type": "break" if seg.note.startswith("30-min break") else (
                        "rest" if seg.note.startswith("10-hr rest") else "fuel"
                    ),
                    "eta": seg.start.isoformat(),
                    "lat": lat,
                    "lon": lon,
                    "duration_hours": (seg.end - seg.start).total_seconds() / 3600.0,
                })
        if seg.status == "D":
            driven_so_far += (seg.end - seg.start).total_seconds() / 3600.0 * (distance_miles / duration_hours if duration_hours > 0 else 0)
    # dropoff at end
    if coords_latlon:
        stops.append({
            "type": "dropoff",
            "eta": hos.segments[-1].end.isoformat(),
            "lat": coords_latlon[-1][0],
            "lon": coords_latlon[-1][1],
            "duration_hours": 1.0,
        })

    return {
        "route": {
            "geometry": route_geo,
            "steps": steps,
        },
        "stops": stops,
        "eld_days": eld_days,
        "summary": {
            "distance_miles": round(distance_miles, 2),
            "duration_hours": round(duration_hours, 2),
        },
    }


