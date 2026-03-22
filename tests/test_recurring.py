"""Tests for recurring transaction endpoints."""


class TestAddRecurring:
    def test_add_recurring_expense(self, client, fresh_user):
        h = fresh_user["header"]
        resp = client.post(
            "/recurring",
            json={
                "amount": 500,
                "transaction_type": "expense",
                "category": "Subscriptions",
                "description": "Netflix",
                "start_date": "2024-01-01",
                "recurrence_rule": {
                    "frequency": "monthly",
                    "interval": 1,
                },
            },
            headers=h,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

    def test_add_recurring_income(self, client, fresh_user):
        h = fresh_user["header"]
        resp = client.post(
            "/recurring",
            json={
                "amount": 5000,
                "transaction_type": "income",
                "category": "Salary",
                "description": "Monthly salary",
                "start_date": "2024-01-01",
                "recurrence_rule": {
                    "frequency": "monthly",
                    "interval": 1,
                },
            },
            headers=h,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

    def test_add_recurring_weekly(self, client, fresh_user):
        h = fresh_user["header"]
        resp = client.post(
            "/recurring",
            json={
                "amount": 100,
                "transaction_type": "expense",
                "category": "Food",
                "description": "Weekly groceries",
                "start_date": "2024-01-01",
                "recurrence_rule": {
                    "frequency": "weekly",
                    "interval": 1,
                },
            },
            headers=h,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

    def test_add_recurring_with_end_date(self, client, fresh_user):
        h = fresh_user["header"]
        resp = client.post(
            "/recurring",
            json={
                "amount": 200,
                "transaction_type": "expense",
                "category": "Gym",
                "description": "Gym membership",
                "start_date": "2024-01-01",
                "recurrence_rule": {
                    "frequency": "monthly",
                    "interval": 1,
                    "end_condition": "on_date",
                    "end_date": "2024-12-31",
                },
            },
            headers=h,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"


class TestGetRecurring:
    def test_get_recurring_list(self, client, fresh_user):
        h = fresh_user["header"]
        client.post(
            "/recurring",
            json={
                "amount": 100,
                "transaction_type": "expense",
                "category": "Food",
                "start_date": "2024-01-01",
                "recurrence_rule": {"frequency": "daily"},
            },
            headers=h,
        )
        resp = client.get("/recurring", headers=h)
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

    def test_get_recurring_detail(self, client, fresh_user):
        h = fresh_user["header"]
        client.post(
            "/recurring",
            json={
                "amount": 100,
                "transaction_type": "expense",
                "category": "Food",
                "start_date": "2024-01-01",
                "recurrence_rule": {"frequency": "daily"},
            },
            headers=h,
        )
        resp = client.get("/recurring/1", headers=h)
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

    def test_get_recurring_invalid_index(self, client, fresh_user):
        h = fresh_user["header"]
        resp = client.get("/recurring/999", headers=h)
        assert resp.json()["status"] == "error"


class TestEditRecurring:
    def test_edit_recurring_template(self, client, fresh_user):
        h = fresh_user["header"]
        client.post(
            "/recurring",
            json={
                "amount": 100,
                "transaction_type": "expense",
                "category": "Food",
                "start_date": "2024-01-01",
                "recurrence_rule": {"frequency": "daily"},
            },
            headers=h,
        )
        resp = client.put(
            "/recurring/1",
            json={
                "edit_action": "edit_template",
                "amount": 200,
                "description": "Updated",
            },
            headers=h,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

    def test_edit_recurring_toggle_active(self, client, fresh_user):
        h = fresh_user["header"]
        client.post(
            "/recurring",
            json={
                "amount": 100,
                "transaction_type": "expense",
                "category": "Food",
                "start_date": "2024-01-01",
                "recurrence_rule": {"frequency": "daily"},
            },
            headers=h,
        )
        resp = client.put(
            "/recurring/1",
            json={"edit_action": "toggle_active"},
            headers=h,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"


class TestDeleteRecurring:
    def test_delete_recurring(self, client, fresh_user):
        h = fresh_user["header"]
        client.post(
            "/recurring",
            json={
                "amount": 100,
                "transaction_type": "expense",
                "category": "Food",
                "start_date": "2024-01-01",
                "recurrence_rule": {"frequency": "daily"},
            },
            headers=h,
        )
        resp = client.delete("/recurring/1", headers=h)
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"


class TestProcessRecurring:
    def test_process_recurring(self, client, fresh_user):
        h = fresh_user["header"]
        resp = client.post("/recurring/process", headers=h)
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"


class TestRecurringTransfer:
    def test_add_recurring_transfer(self, client, fresh_user):
        h = fresh_user["header"]
        client.post("/wallets", json={"name": "Savings"}, headers=h)
        # Switch back — add_wallet switches current wallet
        client.post("/wallets/switch", json={"name": "Main Wallet"}, headers=h)
        resp = client.post(
            "/recurring/transfer",
            json={
                "amount": 1000,
                "target_wallet_name": "Savings",
                "description": "Monthly saving",
                "start_date": "2024-01-01",
                "recurrence_rule": {
                    "frequency": "monthly",
                    "interval": 1,
                },
            },
            headers=h,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"
