"""Live test — the maDMP plugin over the RDMO HTTP API.

Runs against a real RDMO instance (default ``/Users/ot2661/Servers/rdmo-app``)
with ``rdmo_madmp_exporter.urls`` included under ``api/v1/madmp/`` (one line in
``config/urls.py``). Verifies that DRF renders the *same* maDMP as the export
plugin itself, with Token/Basic/Session auth and the RDMO export permission.

Auto-skipped when no RDMO installation is present; run with the RDMO env:

    /Users/ot2661/Servers/rdmo-app/env/bin/python -m pytest tests/test_live_madmp_api.py
"""

import os
import sys
from pathlib import Path

import pytest

from conftest import RDMO_APP

pytestmark = pytest.mark.live

PROJECT_ID = int(os.environ.get("RDMO_PROJECT_ID", "4"))

# The instance's ALLOWED_HOSTS does not list Django's default test host.
TEST_HOST = os.environ.get("RDMO_TEST_HOST", "localhost")

if not RDMO_APP.exists():
    pytest.skip(f"no RDMO instance at {RDMO_APP}", allow_module_level=True)


@pytest.fixture(scope="module")
def django_ready():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    sys.path.insert(0, str(RDMO_APP))
    os.chdir(RDMO_APP)
    import django
    django.setup()


@pytest.fixture(scope="module")
def api_client(django_ready):
    from rest_framework.test import APIClient

    from rdmo.projects.models import Project

    project = Project.objects.get(id=PROJECT_ID)
    owner = project.owners.first() or project.managers.first()
    assert owner is not None, f"project {PROJECT_ID} has no owner/manager user"

    client = APIClient()
    client.force_authenticate(user=owner)
    return client


def test_madmp_endpoint_matches_plugin(api_client):
    from rdmo.projects.models import Project
    from rdmo_madmp_exporter.rdmo import MaDMPExport

    project = Project.objects.get(id=PROJECT_ID)
    export = MaDMPExport("madmp", "as maDMP", "rdmo_madmp_exporter.rdmo.MaDMPExport")
    export.project = project

    response = api_client.get(f"/api/v1/madmp/projects/{PROJECT_ID}/",
                              HTTP_HOST=TEST_HOST)
    assert response.status_code == 200, response.content
    assert response.json() == {"dmp": export.get_dmp()}


def test_madmp_endpoint_requires_authentication(django_ready):
    from rest_framework.test import APIClient

    client = APIClient()
    response = client.get(f"/api/v1/madmp/projects/{PROJECT_ID}/",
                          HTTP_HOST=TEST_HOST)
    assert response.status_code == 401


def test_madmp_endpoint_unknown_project_is_404(api_client):
    response = api_client.get("/api/v1/madmp/projects/999999/",
                              HTTP_HOST=TEST_HOST)
    assert response.status_code == 404
