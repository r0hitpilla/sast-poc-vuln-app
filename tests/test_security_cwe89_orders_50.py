import pytest
import os
import shutil
import sys

# Make `import app` work when pytest runs from the repo root.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import app as app_module
import orders as orders_module


@pytest.fixture
def client():
    # Set up the database and files exactly like the existing tests do
    os.makedirs(orders_module.INVOICE_DIR, exist_ok=True)
    path = os.path.join(orders_module.INVOICE_DIR, "INV-1001.txt")
    with open(path, "w") as f:
        f.write("Invoice 1001: 3 x notebook")
    
    orders_module.init_orders_db()
    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as c:
        yield c
    os.remove(path)
    shutil.rmtree(orders_module.EXPORT_DIR, ignore_errors=True)


def test_proof_sql_injection(client):
    # Control: an ordinary request works and finds a record that really exists
    ok = client.get("/orders/search", query_string={"customer": "ann"})
    assert ok.status_code == 200
    results = ok.get_json()["results"]
    assert len(results) > 0

    # Attack: SQL injection payload that should return no results
    try:
        rows = client.get("/orders/search", query_string={"customer": "nobody' OR '1'='1"}).get_json()["results"]
    except Exception:
        rows = []
    
    assert rows == []  # Safe behavior: no records returned for non-existent customer
