"""Functional tests: legitimate use of every endpoint must keep working.

These deliberately do NOT test that the vulnerabilities are gone: the
autofix pipeline fixes one finding at a time and runs this suite after each
fix, so a test that only passes once *every* bug is fixed would reject each
individual good fix. The scanner checks for the vulnerability; these check
that the fix didn't break the feature.
"""
import os

import pytest

import app as app_module


@pytest.fixture
def client():
    os.makedirs(app_module.UPLOADS_DIR, exist_ok=True)
    sample = os.path.join(app_module.UPLOADS_DIR, "hello.txt")
    with open(sample, "w") as f:
        f.write("hello from uploads")
    app_module.init_db()
    app_module._role_cache.clear()
    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as c:
        yield c
    os.remove(sample)


def test_search_finds_an_existing_user(client):
    resp = client.get("/search?username=alice")
    assert resp.status_code == 200
    assert resp.get_json()["results"] == [{"id": 1, "username": "alice", "role": "admin"}]


def test_search_unknown_user_returns_nothing(client):
    resp = client.get("/search?username=nobody")
    assert resp.status_code == 200
    assert resp.get_json()["results"] == []


def test_files_serves_an_uploaded_file(client):
    resp = client.get("/files/hello.txt")
    assert resp.status_code == 200
    assert resp.data == b"hello from uploads"


def test_admin_data_allows_admin(client):
    resp = client.get("/admin/data?username=alice")
    assert resp.status_code == 200
    assert resp.get_json()["secret"] == "admin-only payload"


def test_admin_data_rejects_regular_user(client):
    resp = client.get("/admin/data?username=bob")
    assert resp.status_code == 403
