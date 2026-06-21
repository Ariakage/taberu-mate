from pathlib import Path

from fastapi.testclient import TestClient

from taberu_mate_backend.core.config import Settings
from taberu_mate_backend.core.security import decode_refresh_token
from taberu_mate_backend.crud.tokens import get_refresh_token
from taberu_mate_backend.db.session import connect
from taberu_mate_backend.main import create_app


def build_client(tmp_path: Path) -> tuple[TestClient, Settings]:
    settings = Settings(
        database_path=tmp_path / "test.db",
        auth_token_secret="test-auth-token-secret-with-enough-length",
        auth_cookie_secure=True,
    )
    return TestClient(create_app(settings), base_url="https://testserver"), settings


def csrf_headers(client: TestClient) -> dict[str, str]:
    response = client.get("/api/v1/auth/csrf")
    assert response.status_code == 200
    token = response.json()["csrf_token"]
    return {"X-CSRF-Token": token}


def test_register_login_and_get_current_user(tmp_path: Path) -> None:
    client, _settings = build_client(tmp_path)
    headers = csrf_headers(client)

    register_response = client.post(
        "/api/v1/auth/register",
        headers=headers,
        json={
            "username": "ariakage",
            "nickname": "Ariakage",
            "avatar_url": "https://example.com/avatar.png",
            "password": "strong-password",
        },
    )

    assert register_response.status_code == 201
    registered_user = register_response.json()
    assert registered_user["username"] == "ariakage"
    assert registered_user["nickname"] == "Ariakage"
    assert registered_user["avatar_url"] == "https://example.com/avatar.png"
    assert "password" not in registered_user
    assert "password_hash" not in registered_user

    login_response = client.post(
        "/api/v1/auth/login",
        headers=headers,
        json={"username": "ariakage", "password": "strong-password"},
    )

    assert login_response.status_code == 200
    token_body = login_response.json()
    assert token_body["token_type"] == "bearer"
    assert token_body["access_token"]
    assert token_body["expires_in"] == 15 * 60
    assert token_body["refresh_expires_in"] == 30 * 24 * 60 * 60
    assert token_body["csrf_token"]

    set_cookie_headers = login_response.headers.get_list("set-cookie")
    assert any("access_token=" in header and "HttpOnly" in header for header in set_cookie_headers)
    assert any("refresh_token=" in header and "HttpOnly" in header for header in set_cookie_headers)
    assert all("Secure" in header for header in set_cookie_headers)
    assert all("SameSite=strict" in header for header in set_cookie_headers)

    me_response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token_body['access_token']}"},
    )

    assert me_response.status_code == 200
    assert me_response.json()["id"] == registered_user["id"]

    cookie_me_response = client.get("/api/v1/users/me")
    assert cookie_me_response.status_code == 200
    assert cookie_me_response.json()["id"] == registered_user["id"]


def test_register_stores_argon2id_hash_and_per_user_salt(tmp_path: Path) -> None:
    client, settings = build_client(tmp_path)
    headers = csrf_headers(client)

    response = client.post(
        "/api/v1/auth/register",
        headers=headers,
        json={
            "username": "hashcheck",
            "nickname": "Hash Check",
            "avatar_url": None,
            "password": "strong-password",
        },
    )

    assert response.status_code == 201

    with connect(settings) as connection:
        row = connection.execute(
            "SELECT password_salt, password_hash FROM users WHERE username = ?",
            ("hashcheck",),
        ).fetchone()

    assert row is not None
    assert row["password_salt"]
    assert row["password_hash"] != "strong-password"
    assert row["password_hash"].startswith("$argon2id$")
    assert f"${row['password_salt']}$" in row["password_hash"]


def test_same_password_uses_different_salts_and_hashes(tmp_path: Path) -> None:
    client, settings = build_client(tmp_path)
    headers = csrf_headers(client)

    first_response = client.post(
        "/api/v1/auth/register",
        headers=headers,
        json={"username": "saltuser1", "avatar_url": None, "password": "strong-password"},
    )
    second_response = client.post(
        "/api/v1/auth/register",
        headers=headers,
        json={"username": "saltuser2", "avatar_url": None, "password": "strong-password"},
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201

    with connect(settings) as connection:
        rows = connection.execute(
            """
            SELECT password_salt, password_hash
            FROM users
            WHERE username IN (?, ?)
            ORDER BY username
            """,
            ("saltuser1", "saltuser2"),
        ).fetchall()

    assert len(rows) == 2
    assert rows[0]["password_salt"] != rows[1]["password_salt"]
    assert rows[0]["password_hash"] != rows[1]["password_hash"]


def test_register_defaults_nickname_to_username(tmp_path: Path) -> None:
    client, _settings = build_client(tmp_path)
    headers = csrf_headers(client)

    response = client.post(
        "/api/v1/auth/register",
        headers=headers,
        json={
            "username": "nonickname",
            "avatar_url": None,
            "password": "strong-password",
        },
    )

    assert response.status_code == 201
    assert response.json()["nickname"] == "nonickname"


def test_duplicate_username_is_rejected_case_insensitively(tmp_path: Path) -> None:
    client, _settings = build_client(tmp_path)
    headers = csrf_headers(client)

    first_response = client.post(
        "/api/v1/auth/register",
        headers=headers,
        json={"username": "MateUser", "avatar_url": None, "password": "strong-password"},
    )
    second_response = client.post(
        "/api/v1/auth/register",
        headers=headers,
        json={"username": "mateuser", "avatar_url": None, "password": "strong-password"},
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409


def test_injection_like_username_is_rejected(tmp_path: Path) -> None:
    client, _settings = build_client(tmp_path)
    headers = csrf_headers(client)

    response = client.post(
        "/api/v1/auth/register",
        headers=headers,
        json={
            "username": "admin';DROP_TABLE_users",
            "avatar_url": None,
            "password": "strong-password",
        },
    )

    assert response.status_code == 422


def test_csrf_is_required_for_state_changing_auth_routes(tmp_path: Path) -> None:
    client, _settings = build_client(tmp_path)

    response = client.post(
        "/api/v1/auth/register",
        json={"username": "csrfcheck", "avatar_url": None, "password": "strong-password"},
    )

    assert response.status_code == 403


def test_refresh_rotates_server_side_refresh_token(tmp_path: Path) -> None:
    client, settings = build_client(tmp_path)
    headers = csrf_headers(client)

    register_response = client.post(
        "/api/v1/auth/register",
        headers=headers,
        json={"username": "rotateuser", "avatar_url": None, "password": "strong-password"},
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        headers=headers,
        json={"username": "rotateuser", "password": "strong-password"},
    )
    assert login_response.status_code == 200
    login_body = login_response.json()
    old_refresh_token = client.cookies.get(settings.refresh_token_cookie_name)
    assert old_refresh_token is not None

    refresh_response = client.post(
        "/api/v1/auth/refresh",
        headers={"X-CSRF-Token": login_body["csrf_token"]},
    )

    assert refresh_response.status_code == 200
    assert refresh_response.json()["access_token"] != login_body["access_token"]
    old_refresh_payload = decode_refresh_token(old_refresh_token, settings)
    with connect(settings) as connection:
        old_record = get_refresh_token(connection, old_refresh_payload.jti)

    assert old_record is not None
    assert old_record.revoked_at is not None
    assert old_record.replaced_by_jti is not None


def test_logout_revokes_access_token_jti(tmp_path: Path) -> None:
    client, _settings = build_client(tmp_path)
    headers = csrf_headers(client)

    register_response = client.post(
        "/api/v1/auth/register",
        headers=headers,
        json={"username": "logoutuser", "avatar_url": None, "password": "strong-password"},
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        headers=headers,
        json={"username": "logoutuser", "password": "strong-password"},
    )
    assert login_response.status_code == 200
    login_body = login_response.json()
    access_token = login_body["access_token"]

    logout_response = client.post(
        "/api/v1/auth/logout",
        headers={
            "Authorization": f"Bearer {access_token}",
            "X-CSRF-Token": login_body["csrf_token"],
        },
    )

    assert logout_response.status_code == 204

    me_response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me_response.status_code == 401


def test_user_profile_defaults_and_update(tmp_path: Path) -> None:
    client, _settings = build_client(tmp_path)
    token_body = login_test_user(client, username="profileuser")
    auth_headers = {
        "Authorization": f"Bearer {token_body['access_token']}",
        "X-CSRF-Token": token_body["csrf_token"],
    }

    default_response = client.get(
        "/api/v1/users/me/profile",
        headers={"Authorization": f"Bearer {token_body['access_token']}"},
    )

    assert default_response.status_code == 200
    default_profile = default_response.json()
    assert default_profile["avoidances"] == []
    assert default_profile["allergies"] == []
    assert default_profile["notes"] == ""
    assert default_profile["updated_at"] is None

    update_response = client.put(
        "/api/v1/users/me/profile",
        headers=auth_headers,
        json={
            "avoidances": [" 香菜 ", "太辣"],
            "allergies": ["花生"],
            "notes": "  少油少盐  ",
        },
    )

    assert update_response.status_code == 200
    updated_profile = update_response.json()
    assert updated_profile["avoidances"] == ["香菜", "太辣"]
    assert updated_profile["allergies"] == ["花生"]
    assert updated_profile["notes"] == "少油少盐"
    assert updated_profile["updated_at"] is not None


def test_order_history_roundtrip_and_dashboard(tmp_path: Path) -> None:
    client, _settings = build_client(tmp_path)
    token_body = login_test_user(client, username="historyuser")
    auth_headers = {
        "Authorization": f"Bearer {token_body['access_token']}",
        "X-CSRF-Token": token_body["csrf_token"],
    }

    profile_response = client.put(
        "/api/v1/users/me/profile",
        headers=auth_headers,
        json={
            "avoidances": ["香菜", "猪肉"],
            "allergies": ["花生"],
            "notes": "有过敏请确认",
        },
    )
    assert profile_response.status_code == 200

    create_response = client.post(
        "/api/v1/users/me/orders",
        headers=auth_headers,
        json={
            "restaurant_name": "食べ友食堂",
            "target_language": "ja",
            "customer_remark": "不要香菜",
            "total_label": "¥1800",
            "total_amount": 1800,
            "items": [
                {
                    "id": "item_gyoza",
                    "name_translated": "煎饺",
                    "quantity": 2,
                }
            ],
            "generated_order": {
                "local_language_order_text": "餃子を二人前お願いします。",
                "total": {"display_text": "¥1800"},
            },
        },
    )

    assert create_response.status_code == 201
    created_order = create_response.json()
    assert created_order["restaurant_name"] == "食べ友食堂"
    assert created_order["target_language"] == "ja"
    assert created_order["items"][0]["quantity"] == 2
    assert created_order["generated_order"]["total"]["display_text"] == "¥1800"

    history_response = client.get(
        "/api/v1/users/me/orders",
        headers={"Authorization": f"Bearer {token_body['access_token']}"},
    )

    assert history_response.status_code == 200
    assert history_response.json()[0]["id"] == created_order["id"]

    dashboard_response = client.get(
        "/api/v1/users/me/dashboard",
        headers={"Authorization": f"Bearer {token_body['access_token']}"},
    )

    assert dashboard_response.status_code == 200
    dashboard = dashboard_response.json()
    assert dashboard["stats"]["avoid_count"] == 2
    assert dashboard["stats"]["allergy_count"] == 1
    assert dashboard["stats"]["order_count"] == 1
    assert dashboard["stats"]["updated_at"] is not None
    assert dashboard["recent_orders"][0]["id"] == created_order["id"]


def test_profile_writes_require_csrf(tmp_path: Path) -> None:
    client, _settings = build_client(tmp_path)
    token_body = login_test_user(client, username="csrffood")

    response = client.put(
        "/api/v1/users/me/profile",
        headers={"Authorization": f"Bearer {token_body['access_token']}"},
        json={"avoidances": ["香菜"], "allergies": [], "notes": ""},
    )

    assert response.status_code == 403


def login_test_user(client: TestClient, *, username: str) -> dict[str, object]:
    headers = csrf_headers(client)
    register_response = client.post(
        "/api/v1/auth/register",
        headers=headers,
        json={"username": username, "avatar_url": None, "password": "strong-password"},
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        headers=headers,
        json={"username": username, "password": "strong-password"},
    )
    assert login_response.status_code == 200
    return login_response.json()
