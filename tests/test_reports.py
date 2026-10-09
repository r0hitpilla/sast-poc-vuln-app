"""Functional tests for reports.py: legitimate use must keep working.

Like tests/test_app.py, these do NOT assert that the weaknesses are gone: the
autofix pipeline fixes one finding at a time and runs this suite after each fix.
"""
import pytest
import requests

import app as app_module


@pytest.fixture
def client():
    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as c:
        yield c


def test_report_is_downloaded_with_an_etag(client):
    resp = client.get("/reports/weekly")
    assert resp.status_code == 200
    assert b"Weekly summary" in resp.data
    assert resp.headers["ETag"]


def test_etag_is_stable_and_differs_between_reports(client):
    first = client.get("/reports/weekly").headers["ETag"]
    assert client.get("/reports/weekly").headers["ETag"] == first
    assert client.get("/reports/monthly").headers["ETag"] != first


def test_unknown_report_is_404(client):
    assert client.get("/reports/nope").status_code == 404


def test_sync_posts_the_report_list(client, monkeypatch):
    calls = []

    class Reply:
        status_code = 202

    def fake_post(url, **kwargs):
        calls.append((url, kwargs))
        return Reply()

    monkeypatch.setattr(requests, "post", fake_post)
    resp = client.post("/reports/sync", headers={"X-Requested-By": "ann"})
    assert resp.status_code == 200 and resp.get_json() == {"status": 202}
    assert calls[0][1]["json"] == {"reports": ["monthly", "weekly"], "requested_by": "ann"}
