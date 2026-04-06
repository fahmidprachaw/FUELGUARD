"""
DRF Serializers for the Petrol Pump app.

Serializers convert Django model instances ↔ Python dicts ↔ JSON.
They also validate incoming data.
"""

from rest_framework import serializers
from .models import Vehicle, FuelLog


class VehicleSerializer(serializers.ModelSerializer):
    """
    Serializes Vehicle model data.
    Used for reading vehicle info in API responses.
    """
    class Meta:
        model = Vehicle
        fields = ['id', 'number', 'last_fuel_date']


class FuelLogSerializer(serializers.ModelSerializer):
    """
    Serializes FuelLog model data.
    Used for creating new fuel log entries.
    """
    class Meta:
        model = FuelLog
        fields = ['id', 'vehicle', 'image', 'created_at']


class FuelCheckSerializer(serializers.Serializer):
    """
    Input serializer for the POST /api/check-fuel/ endpoint.

    Accepts:
        image         - The uploaded number plate image (required)
        manual_number - Fallback vehicle number typed manually (optional)
    """
    image = serializers.ImageField(
        required=False,  # Not strictly required; we handle missing gracefully
        help_text="Photo of the vehicle number plate"
    )
    manual_number = serializers.CharField(
        required=False,
        max_length=50,
        allow_blank=True,
        help_text="Manually enter vehicle number if OCR fails"
    )
