"""Tests for transfer endpoints."""


class TestTransferContext:
    def test_get_transfer_context(self, client, fresh_user):
        h = fresh_user["header"]
        client.post("/wallets", json={"name": "Second"}, headers=h)
        resp = client.get("/transfer", headers=h)
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"


class TestTransfer:
    def test_transfer_between_wallets(self, client, fresh_user):
        h = fresh_user["header"]
        # Add income to source wallet
        client.post(
            "/transactions",
            json={
                "amount": 1000,
                "transaction_type": "income",
                "category": "Salary",
            },
            headers=h,
        )
        # Create second wallet (this switches current wallet)
        client.post("/wallets", json={"name": "Savings"}, headers=h)
        # Switch back to Main Wallet so it's the transfer source
        client.post("/wallets/switch", json={"name": "Main Wallet"}, headers=h)
        # Transfer — uses target_wallet_name (the handler field name)
        resp = client.post(
            "/transfer",
            json={
                "target_wallet_name": "Savings",
                "amount": 500,
                "description": "Save some",
            },
            headers=h,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

    def test_transfer_nonexistent_wallet(self, client, fresh_user):
        h = fresh_user["header"]
        resp = client.post(
            "/transfer",
            json={
                "target_wallet_name": "Nonexistent",
                "amount": 100,
            },
            headers=h,
        )
        assert resp.json()["status"] == "error"

    def test_transfer_cross_currency(self, client, fresh_user):
        h = fresh_user["header"]
        client.post(
            "/transactions",
            json={
                "amount": 10000,
                "transaction_type": "income",
                "category": "Salary",
            },
            headers=h,
        )
        client.post(
            "/wallets", json={"name": "USD Wallet", "currency": "USD"}, headers=h
        )
        # Switch back — add_wallet switches current wallet
        client.post("/wallets/switch", json={"name": "Main Wallet"}, headers=h)
        resp = client.post(
            "/transfer",
            json={
                "target_wallet_name": "USD Wallet",
                "amount": 5000,
                "received_amount": 10.0,
            },
            headers=h,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"
