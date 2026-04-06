"""
Django Admin registrations.
Allows viewing and managing Vehicles and FuelLogs via /admin/
"""

from django.contrib import admin
from .models import Vehicle, FuelLog


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ['number', 'last_fuel_date']  # Columns in list view
    search_fields = ['number']                    # Enable search by plate number
    list_filter = ['last_fuel_date']              # Sidebar filter by date


@admin.register(FuelLog)
class FuelLogAdmin(admin.ModelAdmin):
    list_display = ['vehicle', 'created_at']      # Columns in list view
    list_filter = ['created_at']                  # Sidebar filter by date
    search_fields = ['vehicle__number']           # Search by vehicle number
    readonly_fields = ['created_at']              # Prevent editing timestamps
