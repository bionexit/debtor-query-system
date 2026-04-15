"""
Test cases for Admin Authentication API
"""
import pytest
from datetime import datetime, timedelta
from app.models.models import User, UserRole
from app.core.security import get_password_hash


class TestAdminLogin:
    """Test admin login endpoint"""

    def test_login_success(self, client, admin_user):
        """Test successful login"""
        response = client.post("/api/admin/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["username"] == "admin"
        assert data["role"] == "admin"

    def test_login_invalid_username(self, client, admin_user):
        """Test login with invalid username"""
        response = client.post("/api/admin/auth/login", json={
            "username": "nonexistent",
            "password": "admin123"
        })
        assert response.status_code == 401
        assert "Invalid username or password" in response.json()["detail"]

    def test_login_invalid_password(self, client, admin_user):
        """Test login with invalid password"""
        response = client.post("/api/admin/auth/login", json={
            "username": "admin",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        assert "Invalid password" in response.json()["detail"]

    def test_login_inactive_user(self, client, db_session):
        """Test login with inactive user"""
        user = User(
            username="inactive",
            email="inactive@example.com",
            hashed_password=get_password_hash("pass123"),
            role=UserRole.ADMIN,
            is_active=False
        )
        db_session.add(user)
        db_session.commit()
        
        response = client.post("/api/admin/auth/login", json={
            "username": "inactive",
            "password": "pass123"
        })
        assert response.status_code == 401
        assert "deactivated" in response.json()["detail"]

    def test_login_locked_account(self, client, locked_user):
        """Test login with locked account"""
        response = client.post("/api/admin/auth/login", json={
            "username": "locked",
            "password": "locked123"
        })
        assert response.status_code == 401
        assert "locked" in response.json()["detail"].lower()

    def test_login_multiple_failed_attempts(self, client, admin_user, db_session):
        """Test account locking after multiple failed attempts"""
        # Set user to have 4 failed attempts
        admin_user.failed_login_attempts = 4
        db_session.commit()
        
        # 5th attempt should lock
        response = client.post("/api/admin/auth/login", json={
            "username": "admin",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        assert "locked" in response.json()["detail"].lower()


class TestAdminLogout:
    """Test admin logout endpoint"""

    def test_logout_success(self, client, admin_headers):
        """Test successful logout"""
        response = client.post("/api/admin/auth/logout", headers=admin_headers)
        assert response.status_code == 200
        assert "logged out" in response.json()["message"].lower()

    def test_logout_without_token(self, client):
        """Test logout without token"""
        response = client.post("/api/admin/auth/logout")
        assert response.status_code == 403


class TestChangePassword:
    """Test change password endpoint"""

    def test_change_password_success(self, client, admin_headers, admin_user):
        """Test successful password change"""
        response = client.post(
            "/api/admin/auth/change-password",
            headers=admin_headers,
            json={
                "old_password": "admin123",
                "new_password": "newpassword123"
            }
        )
        assert response.status_code == 200
        assert "successfully" in response.json()["message"].lower()

    def test_change_password_wrong_old(self, client, admin_headers, admin_user):
        """Test password change with wrong old password"""
        response = client.post(
            "/api/admin/auth/change-password",
            headers=admin_headers,
            json={
                "old_password": "wrongoldpassword",
                "new_password": "newpassword123"
            }
        )
        assert response.status_code == 400
        assert "incorrect" in response.json()["detail"].lower()

    def test_change_password_unauthenticated(self, client):
        """Test password change without authentication"""
        response = client.post(
            "/api/admin/auth/change-password",
            json={
                "old_password": "old",
                "new_password": "new"
            }
        )
        assert response.status_code == 403


class TestUnlockUser:
    """Test unlock user endpoint"""

    def test_unlock_user_success(self, client, admin_headers, locked_user, db_session):
        """Test successful user unlock"""
        response = client.post(
            f"/api/admin/auth/unlock/{locked_user.id}",
            headers=admin_headers
        )
        assert response.status_code == 200
        assert "unlocked" in response.json()["message"].lower()
        
        # Verify user is unlocked
        db_session.refresh(locked_user)
        assert not locked_user.is_locked
        assert locked_user.failed_login_attempts == 0

    def test_unlock_nonexistent_user(self, client, admin_headers):
        """Test unlock nonexistent user"""
        response = client.post(
            "/api/admin/auth/unlock/99999",
            headers=admin_headers
        )
        assert response.status_code == 404

    def test_unlock_requires_admin(self, client, operator_headers, locked_user):
        """Test unlock requires admin role"""
        response = client.post(
            f"/api/admin/auth/unlock/{locked_user.id}",
            headers=operator_headers
        )
        assert response.status_code == 403


class TestUserManagement:
    """Test user management endpoints"""

    def test_list_users(self, client, admin_headers, admin_user, operator_user):
        """Test listing users"""
        response = client.get("/api/admin/auth/users", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert len(data["users"]) >= 2

    def test_get_user(self, client, admin_headers, operator_user):
        """Test getting specific user"""
        response = client.get(
            f"/api/admin/auth/users/{operator_user.id}",
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "operator"

    def test_get_nonexistent_user(self, client, admin_headers):
        """Test getting nonexistent user"""
        response = client.get(
            "/api/admin/auth/users/99999",
            headers=admin_headers
        )
        assert response.status_code == 404

    def test_create_user(self, client, admin_headers):
        """Test creating new user"""
        response = client.post(
            "/api/admin/auth/users",
            headers=admin_headers,
            params={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "newpass123",
                "role": "operator"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "newuser"

    def test_create_user_invalid_role(self, client, admin_headers):
        """Test creating user with invalid role"""
        response = client.post(
            "/api/admin/auth/users",
            headers=admin_headers,
            params={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "newpass123",
                "role": "invalid_role"
            }
        )
        assert response.status_code == 400

    def test_create_user_requires_admin(self, client, operator_headers):
        """Test creating user requires admin role"""
        response = client.post(
            "/api/admin/auth/users",
            headers=operator_headers,
            params={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "newpass123",
                "role": "operator"
            }
        )
        assert response.status_code == 403

    def test_update_user(self, client, admin_headers, operator_user):
        """Test updating user"""
        response = client.put(
            f"/api/admin/auth/users/{operator_user.id}",
            headers=admin_headers,
            params={
                "email": "updated@example.com",
                "role": "admin"
            }
        )
        assert response.status_code == 200
        
        # Verify update
        response = client.get(
            f"/api/admin/auth/users/{operator_user.id}",
            headers=admin_headers
        )
        assert response.json()["email"] == "updated@example.com"

    def test_delete_user(self, client, admin_headers, operator_user):
        """Test deleting user"""
        response = client.delete(
            f"/api/admin/auth/users/{operator_user.id}",
            headers=admin_headers
        )
        assert response.status_code == 200
        
        # Verify deletion
        response = client.get(
            f"/api/admin/auth/users/{operator_user.id}",
            headers=admin_headers
        )
        assert response.status_code == 404

    def test_delete_self_not_allowed(self, client, admin_headers, admin_user):
        """Test cannot delete self"""
        response = client.delete(
            f"/api/admin/auth/users/{admin_user.id}",
            headers=admin_headers
        )
        assert response.status_code == 400
        assert "yourself" in response.json()["detail"].lower()
