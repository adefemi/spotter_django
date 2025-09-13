from rest_framework import serializers


class PlanTripRequestSerializer(serializers.Serializer):
    current_location = serializers.CharField()
    pickup_location = serializers.CharField()
    dropoff_location = serializers.CharField()
    current_cycle_hours_used = serializers.FloatField(min_value=0, max_value=70)
    start_time = serializers.DateTimeField(required=False)


class TripSummarySerializer(serializers.Serializer):
    distance_miles = serializers.FloatField()
    duration_hours = serializers.FloatField()


class PlanTripResponseSerializer(serializers.Serializer):
    route = serializers.JSONField(allow_null=True)
    stops = serializers.ListField(child=serializers.DictField(), default=list)
    eld_days = serializers.ListField(child=serializers.DictField(), default=list)
    summary = TripSummarySerializer()


