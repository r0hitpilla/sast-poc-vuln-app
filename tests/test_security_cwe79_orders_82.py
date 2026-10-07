import pytest
import os
import shutil
import sys

# Make `import app` work when pytest runs from the repo root.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import app as app_module
import orders as orders_module

INVOICE = "INV-1001.txt"


@pytest.fixture
def client():
    os.makedirs(orders_module.INVOICE_DIR, exist_ok=True)
    path = os.path.join(orders_module.INVOICE_DIR, INVOICE)
    with open(path, "w") as f:
        f.write("Invoice 1001: 3 x notebook")
    orders_module.init_orders_db()
    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as c:
        yield c
    os.remove(path)
    shutil.rmtree(orders_module.EXPORT_DIR, ignore_errors=True)


def test_proof_script_is_not_reflected(client):
    # Control: normal request should work
    assert client.get("/orders/receipt").status_code == 200

    # Test XSS payload
    try:
        body = client.get("/orders/receipt", query_string={"note": "<script>alert(1)</script>"}).get_data(as_text=True)
    except Exception:
        body = ""
    
    # Test template injection payload
    try:
        math = client.get("/orders/receipt", query_string={"note": "{{1337*3}}"}).get_data(as_text=True)
    except Exception:
        math = ""

    assert "<script>alert(1)</script>" not in body
    assert "4011" not in math
