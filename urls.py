"""
URL configuration for petrol_pump project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render


# ─── Frontend view: serve index.html ─────────────────────────────────────────
def index(request):
    return render(request, 'index.html')


urlpatterns = [
    path('admin/', admin.site.urls),

    # API routes (DRF)
    path('api/', include('app.urls')),

    # Frontend homepage
    path('', index, name='index'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
