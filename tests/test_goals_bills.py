"""Tests for goals and bills endpoints."""


class TestGoals:
    def test_add_goal(self, client, fresh_user):
        h = fresh_user["header"]
        resp = client.post(
            "/goals",
            json={
                "name": "Vacation",
                "target": 50000,
                "goal_description": "Summer vacation fund",
                "currency": "KZT",
            },
            headers=h,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

    def test_get_goals_active(self, client, fresh_user):
        h = fresh_user["header"]
        client.post(
            "/goals",
            json={"name": "Goal1", "target": 1000, "currency": "KZT"},
            headers=h,
        )
        resp = client.get("/goals", params={"filter": "active"}, headers=h)
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

    def test_get_all_goals(self, client, fresh_user):
        h = fresh_user["header"]
        client.post(
            "/goals",
            json={"name": "Goal2", "target": 2000, "currency": "KZT"},
            headers=h,
        )
        resp = client.get("/goals/all", headers=h)
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

    def test_get_goal_detail(self, client, fresh_user):
        h = fresh_user["header"]
        client.post(
            "/goals",
            json={"name": "DetailGoal", "target": 3000, "currency": "KZT"},
            headers=h,
        )
        # Goal wallet name is "Goal: DetailGoal"
        resp = client.get("/goals/Goal: DetailGoal", headers=h)
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

    def test_save_to_goal(self, client, fresh_user):
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
            "/goals",
            json={"name": "SaveGoal", "target": 5000, "currency": "KZT"},
            headers=h,
        )
        resp = client.post(
            "/goals/save",
            json={
                "goal_name": "Goal: SaveGoal",
                "amount": 1000,
            },
            headers=h,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

    def test_complete_goal(self, client, fresh_user):
        h = fresh_user["header"]
        client.post(
            "/goals",
            json={"name": "CompleteMe", "target": 100, "currency": "KZT"},
            headers=h,
        )
        resp = client.post("/goals/Goal: CompleteMe/complete", headers=h)
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

    def test_hide_goal(self, client, fresh_user):
        h = fresh_user["header"]
        client.post(
            "/goals",
            json={"name": "HideMe", "target": 100, "currency": "KZT"},
            headers=h,
        )
        client.post("/goals/Goal: HideMe/complete", headers=h)
        resp = client.post("/goals/Goal: HideMe/hide", headers=h)
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

    def test_reactivate_goal(self, client, fresh_user):
        h = fresh_user["header"]
        client.post(
            "/goals",
            json={"name": "Reactivate", "target": 100, "currency": "KZT"},
            headers=h,
        )
        client.post("/goals/Goal: Reactivate/complete", headers=h)
        resp = client.post("/goals/Goal: Reactivate/reactivate", headers=h)
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

    def test_delete_goal(self, client, fresh_user):
        h = fresh_user["header"]
        client.post(
            "/goals",
            json={"name": "DeleteMe", "target": 100, "currency": "KZT"},
            headers=h,
        )
        # Must complete + hide before deleting
        client.post("/goals/Goal: DeleteMe/complete", headers=h)
        client.post("/goals/Goal: DeleteMe/hide", headers=h)
        resp = client.delete("/goals/Goal: DeleteMe", headers=h)
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

    def test_cannot_delete_active_goal(self, client, fresh_user):
        h = fresh_user["header"]
        client.post(
            "/goals",
            json={"name": "ActiveGoal", "target": 100, "currency": "KZT"},
            headers=h,
        )
        resp = client.delete("/goals/Goal: ActiveGoal", headers=h)
        assert resp.json()["status"] == "error"


class TestBills:
    def test_add_bill(self, client, fresh_user):
        h = fresh_user["header"]
        resp = client.post(
            "/bills",
            json={
                "name": "Rent",
                "target": 150000,
                "goal_description": "Monthly rent",
                "currency": "KZT",
            },
            headers=h,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

    def test_get_bills_active(self, client, fresh_user):
        h = fresh_user["header"]
        client.post(
            "/bills",
            json={"name": "Bill1", "target": 1000, "currency": "KZT"},
            headers=h,
        )
        resp = client.get("/bills", params={"filter": "active"}, headers=h)
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

    def test_get_all_bills(self, client, fresh_user):
        h = fresh_user["header"]
        client.post(
            "/bills",
            json={"name": "Bill2", "target": 2000, "currency": "KZT"},
            headers=h,
        )
        resp = client.get("/bills/all", headers=h)
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

    def test_get_bill_detail(self, client, fresh_user):
        h = fresh_user["header"]
        client.post(
            "/bills",
            json={"name": "DetailBill", "target": 3000, "currency": "KZT"},
            headers=h,
        )
        resp = client.get("/bills/Bill: DetailBill", headers=h)
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

    def test_save_to_bill(self, client, fresh_user):
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
            "/bills",
            json={"name": "SaveBill", "target": 5000, "currency": "KZT"},
            headers=h,
        )
        resp = client.post(
            "/bills/save",
            json={
                "bill_name": "Bill: SaveBill",
                "amount": 1000,
            },
            headers=h,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

    def test_complete_bill(self, client, fresh_user):
        h = fresh_user["header"]
        client.post(
            "/bills",
            json={"name": "CompleteBill", "target": 100, "currency": "KZT"},
            headers=h,
        )
        resp = client.post("/bills/Bill: CompleteBill/complete", headers=h)
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

    def test_hide_bill(self, client, fresh_user):
        h = fresh_user["header"]
        client.post(
            "/bills",
            json={"name": "HideBill", "target": 100, "currency": "KZT"},
            headers=h,
        )
        client.post("/bills/Bill: HideBill/complete", headers=h)
        resp = client.post("/bills/Bill: HideBill/hide", headers=h)
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

    def test_reactivate_bill(self, client, fresh_user):
        h = fresh_user["header"]
        client.post(
            "/bills",
            json={"name": "ReactivateBill", "target": 100, "currency": "KZT"},
            headers=h,
        )
        client.post("/bills/Bill: ReactivateBill/complete", headers=h)
        resp = client.post("/bills/Bill: ReactivateBill/reactivate", headers=h)
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

    def test_delete_bill(self, client, fresh_user):
        h = fresh_user["header"]
        client.post(
            "/bills",
            json={"name": "DeleteBill", "target": 100, "currency": "KZT"},
            headers=h,
        )
        # Must complete + hide before deleting
        client.post("/bills/Bill: DeleteBill/complete", headers=h)
        client.post("/bills/Bill: DeleteBill/hide", headers=h)
        resp = client.delete("/bills/Bill: DeleteBill", headers=h)
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"
