"""
Test cases for Auth API (auth.py)
Covering: login, logout, token refresh, password reset, me
"""
import pytest
from datetime import datetime, timedelta


class TestLogin:
    """Test POST /api/auth/login"""

    def test_login_success(self, client, admin_user):
        """Test successful login with correct credentials"""
        response = client.post(
            "/api/auth/login",
            json={
                "username": "admin",
                "password": "admin123"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data

    def test_login_wrong_password(self, client, admin_user):
        """Test login with wrong password"""
        response = client.post(
            "/api/auth/login",
            json={
                "username": "admin",
                "password": "wrongpassword"
            }
        )
        assert response.status_code == 401
        assert "detail" in response.json()

    def test_login_nonexistent_user(self, client):
        """Test login with non-existent user"""
        response = client.post(
            "/api/auth/login",
            json={
                "username": "nonexistent",
                "password": "somepassword"
            }
        )
        assert response.status_code == 401

    def test_login_missing_fields(self, client):
        """Test login with missing required fields"""
        response = client.post(
            "/api/auth/login",
            json={"username": "admin"}
        )
        assert response.status_code == 422

    def test_login_empty_body(self, client):
        """Test login with empty request body"""
        response = client.post(
            "/api/auth/login",
            json={}
        )
        assert response.status_code == 422


class TestGetCurrentUser:
    """Test GET /api/auth/me"""

    def test_get_me_authenticated(self, client, admin_headers):
        """Test getting current user info when authenticated"""
        response = client.get("/api/auth/me", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "admin"

    def test_get_me_unauthenticated(self, client):
        """Test getting current user info without authentication"""
        response = client.get("/api/auth/me")
        assert response.status_code == 401


class TestRefreshToken:
    """Test POST /api/auth/refresh"""

    def test_refresh_valid_token(self, client, admin_headers):
        """Test refreshing a valid token"""
        response = client.post("/api/auth/refresh", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    def test_refresh_no_token(self, client):
        """Test refresh without token"""
        response = client.post("/api/auth/refresh")
        assert response.status_code == 401


class TestPasswordReset:
    """Test password reset flow"""

    def test_request_password_reset(self, client, admin_user):
        """Test requesting password reset"""
        response = client.post(
            f"/api/auth/password/reset?phone={admin_user.phone}"
        )
        # May return 200 even if phone doesn't exist for security
        assert response.status_code in [200, 404]

    def test_confirm_password_reset_invalid(self, client):
        """Test confirming password reset with invalid code"""
        response = client.post(
            "/api/auth/password/reset/confirm",
            json={
                "phone": "13800138000",
                "sms_code": "000000",
                "new_password": "newpass123"
            }
        )
        assert response.status_code in [400, 404]


class TestLogout:
    """Test POST /api/auth/logout"""

    def test_logout_success(self, client, admin_headers):
        """Test successful logout"""
        response = client.post("/api/auth/logout", headers=admin_headers)
        assert response.status_code == 200

    def test_logout_no_token(self, client):
        """Test logout without token"""
        response = client.post("/api/auth/logout")
        assert response.status_code == 401
