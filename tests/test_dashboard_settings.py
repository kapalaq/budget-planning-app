"""Tests for dashboard, help, settings, and percentages endpoints."""

import pytest


class TestDashboard:
    def test_get_dashboard(self, client, auth_header):
        resp = client.get("/dashboard", headers=auth_header)
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

    def test_get_dashboard_with_transactions(self, client, fresh_user):
        h = fresh_user["header"]
        # Add some transactions
        client.post(
            "/transactions",
            json={
                "amount": 5000,
                "transaction_type": "income",
                "category": "Salary",
            },
            headers=h,
        )
        client.post(
            "/transactions",
            json={
                "amount": 1000,
                "transaction_type": "expense",
                "category": "Food",
            },
            headers=h,
        )
        resp = client.get("/dashboard", headers=h)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"


class TestHelp:
    def test_get_help(self, client, auth_header):
        resp = client.get("/help", headers=auth_header)
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"


class TestLanguageSettings:
    def test_get_language(self, client, auth_header):
        resp = client.get("/settings/language", headers=auth_header)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert "language" in data.get("data", data)

    def test_set_language(self, client, fresh_user):
        h = fresh_user["header"]
        resp = client.post(
            "/settings/language", json={"language": "ru-RU"}, headers=h
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

        # Verify it was set
        resp2 = client.get("/settings/language", headers=h)
        assert resp2.json()["data"]["language"] == "ru-RU"

    def test_set_invalid_language(self, client, fresh_user):
        h = fresh_user["header"]
        resp = client.post(
            "/settings/language", json={"language": "xx-XX"}, headers=h
        )
        assert resp.status_code == 400


class TestPercentages:
    def test_get_percentages_empty(self, client, fresh_user):
        h = fresh_user["header"]
        resp = client.get("/percentages", headers=h)
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

    def test_get_percentages_with_data(self, client, fresh_user):
        h = fresh_user["header"]
        # Add transactions with different categories
        for cat, amt in [("Food", 300), ("Transport", 200), ("Entertainment", 100)]:
            client.post(
                "/transactions",
                json={
                    "amount": amt,
                    "transaction_type": "expense",
                    "category": cat,
                },
                headers=h,
            )
        resp = client.get("/percentages", headers=h)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
