"""maDMP plugin over the RDMO HTTP API (CF1).

RDMO exposes the registered export plugins only through the web UI
(``/projects/{pk}/export/{format}/``, session auth). ``regimo-core`` needs a
machine-to-machine route, so this module adds a small DRF endpoint that
renders the *same* plugin — no second implementation of the mapping.

Deployed in the RDMO instance with one line in ``config/urls.py``::

    path('api/v1/madmp/', include('rdmo_madmp_exporter.urls')),

giving ``GET /api/v1/madmp/projects/{pk}/`` -> ``{"dmp": {...}}``.

Authentication mirrors the RDMO REST API (Basic / Token / Session); the
authorisation check reuses the RDMO export permission
(``projects.export_project_object``), so the endpoint is exactly as strict as
the web export it wraps.
"""

from __future__ import annotations

from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.authentication import (  # noqa: F401 — re-exported for the instance config
    BasicAuthentication,
    SessionAuthentication,
    TokenAuthentication,
)
from rest_framework.response import Response
from rest_framework.views import APIView

PLUGIN_KEY = "madmp"
PLUGIN_LABEL = "as maDMP"
PLUGIN_PATH = "rdmo_madmp_exporter.rdmo.MaDMPExport"


class ProjectMaDMPView(APIView):
    """Render one RDMO project through the registered maDMP export plugin."""

    authentication_classes = (TokenAuthentication, BasicAuthentication,
                               SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, pk: int):
        from rdmo.projects.models import Project
        from rdmo_madmp_exporter.rdmo import MaDMPExport

        project = get_object_or_404(Project.objects.all(), pk=pk)
        if not request.user.has_perm("projects.export_project_object", project):
            return Response(
                {"detail": "You do not have permission to export this project."},
                status=status.HTTP_403_FORBIDDEN,
            )

        export = MaDMPExport(PLUGIN_KEY, PLUGIN_LABEL, PLUGIN_PATH)
        export.request = request
        export.project = project
        return Response({"dmp": export.get_dmp()})
