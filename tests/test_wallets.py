"""Tests for wallet endpoints."""

import secrets

import pytest


class TestGetWallets:
    def test_list_wallets(self, client, auth_header):
        resp = client.get("/wallets", headers=auth_header)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        # New user should have a default "Main Wallet"
        assert "wallets" in data.get("data", data)

    def test_get_wallet_detail(self, client, auth_header):
        resp = client.get("/wallets/Main Wallet", headers=auth_header)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"


class TestAddWallet:
    def test_add_wallet(self, client, fresh_user):
        h = fresh_user["header"]
        resp = client.post(
            "/wallets",
            json={"name": "Savings", "currency": "USD", "description": "My savings"},
            headers=h,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"

        # Verify it appears in wallet list
        resp2 = client.get("/wallets", headers=h)
        wallet_names = [
            w["name"] for w in resp2.json().get("data", resp2.json())["wallets"]
        ]
        assert "Savings" in wallet_names

    def test_add_duplicate_wallet(self, client, fresh_user):
        h = fresh_user["header"]
        client.post("/wallets", json={"name": "Dup"}, headers=h)
        resp = client.post("/wallets", json={"name": "Dup"}, headers=h)
        assert resp.json()["status"] == "error"

    def test_add_deposit_wallet(self, client, fresh_user):
        h = fresh_user["header"]
        resp = client.post(
            "/wallets",
            json={
                "name": "Deposit",
                "currency": "KZT",
                "wallet_type": "deposit",
                "interest_rate": 14.5,
                "term_months": 12,
            },
            headers=h,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"


class TestEditWallet:
    def test_edit_wallet_name(self, client, fresh_user):
        h = fresh_user["header"]
        client.post("/wallets", json={"name": "OldName"}, headers=h)
        resp = client.put(
            "/wallets/OldName",
            json={"new_name": "NewName"},
            headers=h,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

        # Old name should not exist
        resp2 = client.get("/wallets/OldName", headers=h)
        assert resp2.json()["status"] == "error"

    def test_edit_wallet_currency(self, client, fresh_user):
        h = fresh_user["header"]
        client.post(
            "/wallets", json={"name": "CurrTest", "currency": "KZT"}, headers=h
        )
        resp = client.put(
            "/wallets/CurrTest", json={"currency": "USD"}, headers=h
        )
        assert resp.status_code == 200


class TestDeleteWallet:
    def test_delete_wallet(self, client, fresh_user):
        h = fresh_user["header"]
        client.post("/wallets", json={"name": "ToDelete"}, headers=h)
        resp = client.delete("/wallets/ToDelete", headers=h)
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

    def test_delete_nonexistent_wallet(self, client, fresh_user):
        h = fresh_user["header"]
        resp = client.delete("/wallets/Nonexistent", headers=h)
        assert resp.json()["status"] == "error"

    def test_delete_last_wallet(self, client, fresh_user):
        h = fresh_user["header"]
        # fresh user only has "Main Wallet" — backend allows deletion
        resp = client.delete("/wallets/Main Wallet", headers=h)
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"


class TestSwitchWallet:
    def test_switch_wallet(self, client, fresh_user):
        h = fresh_user["header"]
        client.post("/wallets", json={"name": "Second"}, headers=h)
        resp = client.post(
            "/wallets/switch", json={"name": "Second"}, headers=h
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

    def test_switch_nonexistent(self, client, fresh_user):
        h = fresh_user["header"]
        resp = client.post(
            "/wallets/switch", json={"name": "Nope"}, headers=h
        )
        assert resp.json()["status"] == "error"
