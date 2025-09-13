# Spotter Backend (Django + DRF)

Trip planning API that computes a driving route, inserts legally required stops per FMCSA Hours of Service (HOS), and returns ELD log segments.

## Stack
- Django 4.2 + Django REST Framework
- Geocoding: Nominatim (OpenStreetMap)
- Routing: OSRM public server (GeoJSON geometry)
- Containerized via Docker

## API

### POST /api/plan-trip/
Plan a trip from current → pickup → dropoff with HOS scheduling.

Request JSON
```json
{
  "current_location": "San Francisco, CA",
  "pickup_location": "Los Angeles, CA",
  "dropoff_location": "Las Vegas, NV",
  "current_cycle_hours_used": 0,
  "start_time": "2025-09-13T08:00:00Z"
}
```

Response JSON (shape)
```json
{
  "route": {
    "geometry": { "type": "LineString", "coordinates": [[-122.4,37.7], ...] },
    "steps": [ ]
  },
  "stops": [
    { "type": "pickup", "eta": "2025-09-13T08:00:00Z", "lat": 37.7, "lon": -122.4, "duration_hours": 1.0 }
  ],
  "eld_days": [
    { "date": "2025-09-13", "segments": [ { "start": "...", "end": "...", "status": "ON", "note": "Pickup loading" } ] }
  ],
  "summary": { "distance_miles": 661.14, "duration_hours": 12.31 }
}
```

Curl
```bash
curl -s http://localhost:8000/api/plan-trip/ \
  -H "Content-Type: application/json" \
  -d '{
    "current_location": "San Francisco, CA",
    "pickup_location": "Los Angeles, CA",
    "dropoff_location": "Las Vegas, NV",
    "current_cycle_hours_used": 0
  }' | jq .
```

## HOS rules (simplified)
- Property-carrying driver (70 hrs in 8 days)
- 1 h on-duty at pickup and at dropoff
- 30-min break after 8 hours driving
- Max 11 h driving and 14 h on-duty window; then 10 h rest
- 34 h restart when the 70 h cycle is exceeded
- Fuel stop every ~1000 miles (0.5 h on-duty)

Notes
- ETAs use routing durations, not live traffic
- Timezone simplified (client local display)

## Local development

Prereqs: Docker and Docker Compose.

```bash
cd spotter_django
# optional: create .env to override settings (not required for OSRM/Nominatim)
docker-compose up -d --build
```

Backend: http://localhost:8000

Run tests
```bash
docker-compose exec web python manage.py test trips -v 2
```

## Deployment

Backend (Render)
1. Push repo to GitHub
2. New Web Service → Root: `spotter_django` (Dockerfile detected)
3. Port 8000, Command: `python manage.py runserver 0.0.0.0:8000`
4. Env: `DJANGO_SETTINGS_MODULE=spotter_django.settings`

Frontend (Vercel)
1. Import `spotter-react`
2. Env: `VITE_API_BASE` = your backend URL

## Services used
- Nominatim (geocoding): public endpoint, set a valid User-Agent with contact in `trips/nominatim.py`
- OSRM (routing): public `router.project-osrm.org`

## Hardening
- Set `DEBUG=False`, restrict `ALLOWED_HOSTS`
- Lock CORS to your frontend domain
