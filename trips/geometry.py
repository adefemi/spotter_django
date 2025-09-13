from typing import List, Tuple


def cumulative_distances(coords: List[Tuple[float, float]]) -> List[float]:
    # Haversine in miles
    import math
    R = 3958.7613
    out = [0.0]
    for i in range(1, len(coords)):
        lat1, lon1 = coords[i - 1]
        lat2, lon2 = coords[i]
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        out.append(out[-1] + R * c)
    return out


def interpolate_point(coords: List[Tuple[float, float]], cumdist: List[float], target_miles: float) -> Tuple[float, float]:
    if not coords:
        raise ValueError("No geometry coordinates")
    if target_miles <= 0:
        return coords[0]
    if target_miles >= cumdist[-1]:
        return coords[-1]
    # find segment
    import bisect
    idx = bisect.bisect_left(cumdist, target_miles)
    if cumdist[idx] == target_miles:
        return coords[idx]
    # interpolate between idx-1 and idx
    d0 = cumdist[idx - 1]
    d1 = cumdist[idx]
    t = (target_miles - d0) / (d1 - d0)
    lat0, lon0 = coords[idx - 1]
    lat1, lon1 = coords[idx]
    return (lat0 + t * (lat1 - lat0), lon0 + t * (lon1 - lon0))


