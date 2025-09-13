from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django.utils import timezone
from .serializers import PlanTripRequestSerializer, PlanTripResponseSerializer
from .planner import plan_trip as plan_trip_service


class PlanTripAPIView(APIView):
    def post(self, request):
        request_serializer = PlanTripRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)

        validated = request_serializer.validated_data
        start_time = validated.get("start_time") or timezone.now()
        try:
            response_data = plan_trip_service(
                current_location=validated["current_location"],
                pickup_location=validated["pickup_location"],
                dropoff_location=validated["dropoff_location"],
                cycle_hours_used=validated["current_cycle_hours_used"],
                start_time=start_time,
            )
        except Exception as exc:
            return Response({"error": "plan_failed", "detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        response_serializer = PlanTripResponseSerializer(response_data)
        return Response(response_serializer.data, status=status.HTTP_200_OK)

