"""Tests for authentication endpoints."""

import secrets

import pytest


class TestHealthCheck:
    def test_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"


class TestRegister:
    def test_register_success(self, client):
        login = f"reg_{secrets.token_hex(4)}"
        resp = client.post(
            "/auth/register", json={"login": login, "password": "pass123"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert "token" in data
        assert "user_id" in data

    def test_register_duplicate_login(self, client):
        login = f"dup_{secrets.token_hex(4)}"
        client.post("/auth/register", json={"login": login, "password": "p1"})
        resp = client.post(
            "/auth/register", json={"login": login, "password": "p2"}
        )
        assert resp.status_code == 409

    def test_register_with_telegram_id(self, client):
        login = f"tg_{secrets.token_hex(4)}"
        tg_id = f"tg{secrets.token_hex(4)}"
        resp = client.post(
            "/auth/register",
            json={"login": login, "password": "p", "telegram_id": tg_id},
        )
        assert resp.status_code == 200
        # Should be able to auth via telegram now
        resp2 = client.post("/auth/telegram", json={"telegram_id": tg_id})
        assert resp2.status_code == 200


class TestLogin:
    def test_login_success(self, client, registered_user):
        resp = client.post(
            "/auth/login",
            json={
                "login": registered_user["login"],
                "password": registered_user["password"],
            },
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"
        assert "token" in resp.json()

    def test_login_wrong_password(self, client, registered_user):
        resp = client.post(
            "/auth/login",
            json={"login": registered_user["login"], "password": "wrong"},
        )
        assert resp.status_code == 401

    def test_login_nonexistent_user(self, client):
        resp = client.post(
            "/auth/login", json={"login": "nonexistent", "password": "x"}
        )
        assert resp.status_code == 401


class TestTelegramAuth:
    def test_telegram_auth_not_linked(self, client):
        resp = client.post(
            "/auth/telegram", json={"telegram_id": "unknown_id"}
        )
        assert resp.status_code == 404

    def test_telegram_auth_missing_id(self, client):
        resp = client.post("/auth/telegram", json={})
        assert resp.status_code == 400


class TestLinkCode:
    def test_link_code_flow(self, client, auth_header):
        # Generate link code
        resp = client.post("/auth/link-code", headers=auth_header)
        assert resp.status_code == 200
        data = resp.json()
        assert "code" in data
        assert "deep_link" in data
        assert data["code"]

    def test_telegram_link(self, client, auth_header):
        # Generate link code
        resp = client.post("/auth/link-code", headers=auth_header)
        code = resp.json()["code"]

        tg_id = f"link_{secrets.token_hex(4)}"
        resp2 = client.post(
            "/auth/telegram-link", json={"code": code, "telegram_id": tg_id}
        )
        assert resp2.status_code == 200
        assert resp2.json()["status"] == "success"

    def test_telegram_link_invalid_code(self, client):
        resp = client.post(
            "/auth/telegram-link",
            json={"code": "invalid", "telegram_id": "123"},
        )
        assert resp.status_code == 400

    def test_telegram_link_missing_fields(self, client):
        resp = client.post("/auth/telegram-link", json={})
        assert resp.status_code == 400


class TestUnlinkTelegram:
    def test_unlink(self, client):
        # Register with telegram
        login = f"unlink_{secrets.token_hex(4)}"
        tg_id = f"untg_{secrets.token_hex(4)}"
        client.post(
            "/auth/register",
            json={"login": login, "password": "p", "telegram_id": tg_id},
        )
        # Unlink
        resp = client.post(
            "/auth/unlink-telegram", json={"telegram_id": tg_id}
        )
        assert resp.status_code == 200

        # Should no longer be able to auth via telegram
        resp2 = client.post("/auth/telegram", json={"telegram_id": tg_id})
        assert resp2.status_code == 404

    def test_unlink_missing_id(self, client):
        resp = client.post("/auth/unlink-telegram", json={})
        assert resp.status_code == 400


class TestAuthRequired:
    def test_no_header(self, client):
        resp = client.get("/dashboard")
        assert resp.status_code == 422  # missing header

    def test_invalid_token(self, client):
        resp = client.get(
            "/dashboard", headers={"Authorization": "Bearer invalid_token"}
        )
        assert resp.status_code == 401
