"""
URL routes for the 'app' application.
These are prefixed with /api/ in the root urls.py.
"""

from django.urls import path
from .views import CheckFuelView

urlpatterns = [
    # POST /api/check-fuel/
    # Main endpoint: accepts image, returns allow/block/error
    path('check-fuel/', CheckFuelView.as_view(), name='check-fuel'),
]
