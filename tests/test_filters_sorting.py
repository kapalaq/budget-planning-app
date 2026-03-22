"""Tests for filter and sorting endpoints."""


class TestSorting:
    def test_get_sorting_options(self, client, auth_header):
        resp = client.get("/sorting", headers=auth_header)
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

    def test_set_sorting(self, client, fresh_user):
        h = fresh_user["header"]
        resp = client.post(
            "/sorting",
            json={"strategy_key": "1"},
            headers=h,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

    def test_get_wallet_sorting_options(self, client, auth_header):
        resp = client.get("/sorting/wallets", headers=auth_header)
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

    def test_set_wallet_sorting(self, client, fresh_user):
        h = fresh_user["header"]
        resp = client.post(
            "/sorting/wallets",
            json={"strategy_key": "1"},
            headers=h,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"


class TestFilters:
    def test_get_active_filters_empty(self, client, fresh_user):
        h = fresh_user["header"]
        resp = client.get("/filters", headers=h)
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

    def test_add_filter_by_category(self, client, fresh_user):
        h = fresh_user["header"]
        resp = client.post(
            "/filters",
            json={"filter_type": "category", "categories": ["Food"]},
            headers=h,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

    def test_add_filter_expense_only(self, client, fresh_user):
        h = fresh_user["header"]
        resp = client.post(
            "/filters", json={"filter_type": "expense_only"}, headers=h
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

    def test_add_filter_income_only(self, client, fresh_user):
        h = fresh_user["header"]
        resp = client.post(
            "/filters", json={"filter_type": "income_only"}, headers=h
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

    def test_add_filter_date_range(self, client, fresh_user):
        h = fresh_user["header"]
        resp = client.post(
            "/filters",
            json={
                "filter_type": "date_range",
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
            },
            headers=h,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

    def test_add_filter_amount_range(self, client, fresh_user):
        h = fresh_user["header"]
        resp = client.post(
            "/filters",
            json={
                "filter_type": "amount_range",
                "min_amount": 100,
                "max_amount": 500,
            },
            headers=h,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

    def test_remove_filter(self, client, fresh_user):
        h = fresh_user["header"]
        client.post(
            "/filters", json={"filter_type": "expense_only"}, headers=h
        )
        resp = client.delete("/filters/0", headers=h)
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

    def test_clear_filters(self, client, fresh_user):
        h = fresh_user["header"]
        client.post(
            "/filters", json={"filter_type": "expense_only"}, headers=h
        )
        client.post(
            "/filters",
            json={"filter_type": "category", "categories": ["Food"]},
            headers=h,
        )
        resp = client.delete("/filters", headers=h)
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

    def test_add_preset_filters(self, client, fresh_user):
        h = fresh_user["header"]
        # "this_week" is not a valid preset; valid ones: today, last_week, this_month, etc.
        for preset in ["today", "last_week", "this_month", "this_year"]:
            resp = client.post(
                "/filters", json={"filter_type": preset}, headers=h
            )
            assert resp.status_code == 200
            assert resp.json()["status"] == "success"
            client.delete("/filters", headers=h)
