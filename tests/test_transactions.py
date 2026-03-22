"""Tests for transaction endpoints."""

import secrets

import pytest


class TestAddTransaction:
    def test_add_expense(self, client, fresh_user):
        h = fresh_user["header"]
        resp = client.post(
            "/transactions",
            json={
                "amount": 100.50,
                "transaction_type": "expense",
                "category": "Food",
                "description": "Lunch",
            },
            headers=h,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

    def test_add_income(self, client, fresh_user):
        h = fresh_user["header"]
        resp = client.post(
            "/transactions",
            json={
                "amount": 5000,
                "transaction_type": "income",
                "category": "Salary",
                "description": "Monthly salary",
            },
            headers=h,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

    def test_add_transaction_with_date(self, client, fresh_user):
        h = fresh_user["header"]
        resp = client.post(
            "/transactions",
            json={
                "amount": 250,
                "transaction_type": "expense",
                "category": "Food",
                "description": "Dated transaction",
                "date": "2024-06-15",
            },
            headers=h,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"


class TestGetTransaction:
    def test_get_transaction(self, client, fresh_user):
        h = fresh_user["header"]
        # Add a transaction first
        client.post(
            "/transactions",
            json={
                "amount": 200,
                "transaction_type": "expense",
                "category": "Transport",
            },
            headers=h,
        )
        resp = client.get("/transactions/1", headers=h)
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

    def test_get_transaction_invalid_index(self, client, fresh_user):
        h = fresh_user["header"]
        resp = client.get("/transactions/999", headers=h)
        assert resp.json()["status"] == "error"


class TestEditTransaction:
    def test_edit_transaction(self, client, fresh_user):
        h = fresh_user["header"]
        client.post(
            "/transactions",
            json={
                "amount": 50,
                "transaction_type": "expense",
                "category": "Food",
                "description": "Original",
            },
            headers=h,
        )
        resp = client.put(
            "/transactions/1",
            json={"amount": 75, "description": "Edited"},
            headers=h,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

    def test_edit_nonexistent(self, client, fresh_user):
        h = fresh_user["header"]
        resp = client.put(
            "/transactions/999", json={"amount": 10}, headers=h
        )
        assert resp.json()["status"] == "error"


class TestDeleteTransaction:
    def test_delete_transaction(self, client, fresh_user):
        h = fresh_user["header"]
        client.post(
            "/transactions",
            json={
                "amount": 30,
                "transaction_type": "expense",
                "category": "Food",
            },
            headers=h,
        )
        resp = client.delete("/transactions/1", headers=h)
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

    def test_delete_invalid_index(self, client, fresh_user):
        h = fresh_user["header"]
        resp = client.delete("/transactions/999", headers=h)
        assert resp.json()["status"] == "error"


class TestCategories:
    def test_get_expense_categories(self, client, auth_header):
        resp = client.get(
            "/categories", params={"transaction_type": "expense"}, headers=auth_header
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"
        assert "categories" in resp.json().get("data", resp.json())

    def test_get_income_categories(self, client, auth_header):
        resp = client.get(
            "/categories", params={"transaction_type": "income"}, headers=auth_header
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"


class TestSuggestAmount:
    def test_suggest_amount(self, client, fresh_user):
        h = fresh_user["header"]
        # Add some transactions with same category
        for amt in [100, 200, 150]:
            client.post(
                "/transactions",
                json={
                    "amount": amt,
                    "transaction_type": "expense",
                    "category": "Food",
                },
                headers=h,
            )
        resp = client.get(
            "/suggest-amount",
            params={"category": "Food", "transaction_type": "expense"},
            headers=h,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"
