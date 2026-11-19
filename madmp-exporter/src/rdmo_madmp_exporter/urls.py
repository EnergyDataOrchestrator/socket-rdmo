"""URLs for the maDMP-over-API endpoint (see ``api.py``).

Included by the RDMO instance under ``api/v1/madmp/``::

    # config/urls.py
    path('api/v1/madmp/', include('rdmo_madmp_exporter.urls')),
"""

from django.urls import path

from rdmo_madmp_exporter.api import ProjectMaDMPView

app_name = "rdmo_madmp_exporter"

urlpatterns = [
    path("projects/<int:pk>/", ProjectMaDMPView.as_view(), name="project-madmp"),
]
