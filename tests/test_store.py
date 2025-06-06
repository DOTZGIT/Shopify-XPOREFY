import tempfile
import json
import os
import importlib

import sys
sys.path.insert(0, str(os.path.dirname(os.path.dirname(__file__))))
import export_shopify as es


def test_save_and_load_store(tmp_path, monkeypatch):
    test_file = tmp_path / "stores.json"
    monkeypatch.setattr(es, "STORE_FILE", str(test_file))

    store = {
        "store_name": "teststore",
        "store_url": "test.myshopify.com",
        "api_key": "key",
        "api_secret_key": "secret",
        "admin_access_token": "token",
    }

    es.save_store(store)
    loaded = es.load_stores()
    assert store["store_url"] in loaded
    assert loaded[store["store_url"]]["api_key"] == "key"
