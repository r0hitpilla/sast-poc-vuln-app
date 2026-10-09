"""Functional tests for tickets.py: legitimate use must keep working.

Like tests/test_app.py, these do NOT assert that the vulnerabilities are gone:
the autofix pipeline fixes one finding at a time and runs this suite after
each fix. The scanner checks for the bug; these check the fix kept the feature.
"""
import pytest

import app as app_module
import tickets as tickets_module

ANN = {"X-Api-Token": "tok-ann"}


@pytest.fixture
def client():
    tickets_module.init_tickets_db()
    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as c:
        yield c


def test_search_lists_own_tickets_sorted_by_date(client):
    resp = client.get("/tickets/search", headers=ANN)
    assert resp.status_code == 200
    assert [r["id"] for r in resp.get_json()["results"]] == [1, 2]


def test_search_filters_by_subject(client):
    resp = client.get("/tickets/search?q=Refund", headers=ANN)
    assert resp.status_code == 200
    assert [r["subject"] for r in resp.get_json()["results"]] == ["Refund request"]


def test_search_can_sort_by_subject(client):
    resp = client.get("/tickets/search?sort=subject", headers=ANN)
    assert resp.status_code == 200
    assert [r["subject"] for r in resp.get_json()["results"]] == ["Login loop", "Refund request"]


def test_search_requires_a_token(client):
    assert client.get("/tickets/search").status_code == 401


def test_owner_can_read_their_ticket(client):
    resp = client.get("/tickets/2", headers=ANN)
    assert resp.status_code == 200
    assert resp.get_json()["subject"] == "Refund request"


def test_missing_ticket_is_404(client):
    assert client.get("/tickets/999", headers=ANN).status_code == 404


def test_owner_can_close_their_ticket(client):
    resp = client.post("/tickets/1/close", headers=ANN)
    assert resp.status_code == 200
    assert client.get("/tickets/1", headers=ANN).get_json()["status"] == "closed"
