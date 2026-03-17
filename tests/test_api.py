"""API endpoint tests for ChainTrack."""

import pytest


class TestHealthEndpoint:
    def test_health_check(self, app_client):
        resp = app_client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["service"] == "chaintrack"

    def test_api_info(self, app_client):
        resp = app_client.get("/api/info")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "ChainTrack"
        assert "SHA-256 hash chain" in data["features"]


class TestProductAPI:
    def test_create_product(self, app_client):
        payload = {
            "name": "API Test Widget",
            "sku": "ATW-001",
            "category": "electronics",
            "manufacturer": "API Corp",
            "weight_kg": 2.5,
        }
        resp = app_client.post("/api/products", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "API Test Widget"
        assert data["tracking_id"].startswith("CT-")
        assert data["current_stage"] == "manufactured"

    def test_list_products(self, app_client):
        # Create a product first
        app_client.post("/api/products", json={
            "name": "List Test", "sku": "LT-001",
        })
        resp = app_client.get("/api/products")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_get_product_not_found(self, app_client):
        resp = app_client.get("/api/products/nonexistent")
        assert resp.status_code == 404


class TestChainAPI:
    def test_record_and_get_chain(self, app_client):
        # Create product
        resp = app_client.post("/api/products", json={
            "name": "Chain Test", "sku": "CHT-001",
        })
        product = resp.json()

        # Record an event
        resp = app_client.post("/api/chain/event", json={
            "product_id": product["id"],
            "event_type": "shipped",
            "location": "Test Port",
            "actor": "tester",
        })
        assert resp.status_code == 201
        block = resp.json()
        assert block["event_type"] == "shipped"
        assert block["block_index"] >= 1  # genesis is 0

        # Get chain
        resp = app_client.get(f"/api/chain/{product['id']}")
        assert resp.status_code == 200
        chain = resp.json()
        assert len(chain) >= 2  # genesis + shipped

    def test_verify_valid_chain(self, app_client):
        resp = app_client.post("/api/products", json={
            "name": "Verify Test", "sku": "VT-001",
        })
        product = resp.json()

        resp = app_client.get(f"/api/verify/{product['id']}")
        assert resp.status_code == 200
        result = resp.json()
        assert result["is_valid"] is True
