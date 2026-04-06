
from django.utils import timezone
from datetime import timedelta

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser

from .models import Vehicle, FuelLog
from .serializers import FuelCheckSerializer
from .utils import extract_vehicle_number


# How many days must pass before a vehicle can refuel
REFUEL_COOLDOWN_DAYS = 3


class CheckFuelView(APIView):
    """
    POST /api/check-fuel/

    Accepts multipart form data:
        image         (file)   - Required: photo of vehicle number plate
        manual_number (string) - Optional: manual fallback if OCR fails

    Returns JSON:
        { "status": "allowed",  "number": "XYZ123" }  → Fuel dispensed
        { "status": "blocked",  "number": "XYZ123" }  → Too soon to refuel
        { "status": "error",    "message": "..."    }  → OCR failed / bad input
    """

    # Allow file uploads via multipart/form-data
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        # ── Step 1: Validate incoming data with serializer ────────────────────
        serializer = FuelCheckSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"status": "error", "message": "Invalid input data."},
                status=status.HTTP_400_BAD_REQUEST
            )

        image_file = serializer.validated_data.get('image')
        manual_number = serializer.validated_data.get('manual_number', '').strip().upper()

        # ── Step 2: Determine vehicle number ──────────────────────────────────
        vehicle_number = None

        if image_file:
            # Try OCR first if an image was uploaded
            vehicle_number = extract_vehicle_number(image_file)

        # If OCR failed or no image, use manual number as fallback
        if not vehicle_number and manual_number:
            vehicle_number = manual_number
            print(f"[View] Using manually entered number: {vehicle_number}")

        # If we still have no number, return an error
        if not vehicle_number:
            return Response(
                {
                    "status": "error",
                    "message": "Number not detected. Please try a clearer image or enter the number manually."
                },
                status=status.HTTP_200_OK  # HTTP 200 but with error status in body
            )

        # ── Step 3: Look up or create the vehicle record ───────────────────────
        # get_or_create returns (instance, created_bool)
        vehicle, created = Vehicle.objects.get_or_create(
            number=vehicle_number,
            defaults={'last_fuel_date': None}
        )

        # ── Step 4: Check the 3-day cooldown rule ─────────────────────────────
        now = timezone.now()

        if vehicle.last_fuel_date is not None:
            # Calculate how much time has passed since last fueling
            time_since_last_fuel = now - vehicle.last_fuel_date
            cooldown_period = timedelta(days=REFUEL_COOLDOWN_DAYS)

            if time_since_last_fuel < cooldown_period:
                # ── BLOCKED: Vehicle fueled too recently ──────────────────────
                next_refuel_time = vehicle.last_fuel_date + cooldown_period
                days_remaining = (cooldown_period - time_since_last_fuel).days
                hours_remaining = int(
                    (cooldown_period - time_since_last_fuel).total_seconds() / 3600
                )

                return Response(
                    {
                        "status": "blocked",
                        "number": vehicle_number,
                        "last_fuel_date": vehicle.last_fuel_date.astimezone(timezone.get_current_timezone()).strftime('%Y-%m-%d %H:%M'),
                        "next_refuel_date": next_refuel_time.astimezone(timezone.get_current_timezone()).strftime('%d %b %Y, %I:%M %p'),
                        "hours_remaining": hours_remaining,
                        "message": f"This vehicle was fueled {hours_remaining} hour(s) ago. "
                                   f"Please wait {days_remaining} more day(s)."
                    },
                    status=status.HTTP_200_OK
                )

        # ── Step 5: ALLOWED – update record and log the fueling ───────────────
        # Update last_fuel_date to now
        vehicle.last_fuel_date = now
        vehicle.save()

        # Create a FuelLog entry (image may or may not exist)
        if image_file:
            # Reset file pointer since it was already read by OCR
            image_file.seek(0)
            FuelLog.objects.create(vehicle=vehicle, image=image_file)
        # If no image (manual number only), skip log image — still record the event

        return Response(
            {
                "status": "allowed",
                "number": vehicle_number,
                "fueled_at": now.strftime('%Y-%m-%d %H:%M'),
                "message": f"Fuel dispensed for vehicle {vehicle_number}."
            },
            status=status.HTTP_200_OK
        )
