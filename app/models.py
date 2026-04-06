"""
Models for the Petrol Pump Fuel Control System.

Two models:
  - Vehicle: tracks each registered vehicle and its last fueling date
  - FuelLog: stores each fueling attempt with the uploaded image
"""

from django.db import models


class Vehicle(models.Model):
    """
    Represents a vehicle that visits the petrol pump.

    Fields:
        number       - Unique vehicle registration number (e.g. "DH1234AB")
        last_fuel_date - When the vehicle was last fueled (null if never)
    """
    number = models.CharField(
        max_length=50,
        unique=True,
        help_text="Vehicle registration number (uppercase letters and digits)"
    )
    last_fuel_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date/time of last successful fueling"
    )

    def __str__(self):
        return self.number

    class Meta:
        verbose_name = "Vehicle"
        verbose_name_plural = "Vehicles"
        ordering = ['number']


class FuelLog(models.Model):
    """
    Records every fuel dispensing event.

    Fields:
        vehicle    - The vehicle that was fueled (FK → Vehicle)
        image      - Uploaded photo of the vehicle number plate
        created_at - Timestamp auto-set when record is created
    """
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,  # Delete logs if vehicle is deleted
        related_name='fuel_logs',
        help_text="Vehicle that received fuel"
    )
    image = models.ImageField(
        upload_to='fuel_logs/',  # Saved to MEDIA_ROOT/fuel_logs/
        help_text="Photo of the vehicle number plate"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,  # Automatically set on creation
        help_text="Timestamp of when this log was created"
    )

    def __str__(self):
        return f"{self.vehicle.number} @ {self.created_at.strftime('%Y-%m-%d %H:%M')}"

    class Meta:
        verbose_name = "Fuel Log"
        verbose_name_plural = "Fuel Logs"
        ordering = ['-created_at']  # Newest first
