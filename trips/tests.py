from datetime import datetime
from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient

from .hos import HOSPlanner


class HOSPlannerTests(TestCase):
    def test_break_and_rest_insertion(self):
        start = datetime(2024, 1, 1, 8, 0, 0)
        hos = HOSPlanner(start_time=start, cycle_hours_used=0)
        hos.drive(20)  # long drive forces break and rest cycles
        # Should include at least one 30-min break and one 10-hr rest
        has_break = any(seg.note.startswith("30-min break") for seg in hos.segments)
        has_rest = any(seg.note.startswith("10-hr rest") for seg in hos.segments)
        self.assertTrue(has_break)
        self.assertTrue(has_rest)


class PlanTripEndpointTests(TestCase):
    @patch("trips.planner.NominatimGeocoder")
    @patch("trips.planner.OSRMClient")
    def test_plan_trip_success(self, mock_osrm_cls, mock_geo_cls):
        mock_geo = mock_geo_cls.return_value
        mock_geo.geocode.side_effect = [
            (37.7749, -122.4194),  # current
            (34.0522, -118.2437),  # pickup
            (36.1699, -115.1398),  # drop
        ]
        mock_osrm = mock_osrm_cls.return_value
        mock_osrm.directions.return_value = {
            "routes": [
                {
                    "summary": {"duration": 6 * 3600, "distance": 800 * 1609.34},
                    "geometry": {"type": "LineString", "coordinates": []},
                    "legs": [],
                }
            ]
        }

        client = APIClient()
        payload = {
            "current_location": "San Francisco, CA",
            "pickup_location": "Los Angeles, CA",
            "dropoff_location": "Las Vegas, NV",
            "current_cycle_hours_used": 0,
        }
        res = client.post("/api/plan-trip/", payload, format="json")
        self.assertEqual(res.status_code, 200)
        self.assertIn("summary", res.data)
        self.assertEqual(res.data["summary"]["distance_miles"], 800.0)
        self.assertEqual(res.data["summary"]["duration_hours"], 6.0)

