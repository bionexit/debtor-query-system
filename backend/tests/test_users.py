"""
Test cases for Users API (users.py)
Covering: user CRUD, role management, batch operations
"""
import pytest


class TestListUsers:
    """Test GET /api/users/"""

    def test_list_users_as_admin(self, client, admin_headers):
        """Test listing users as admin"""
        response = client.get("/api/users/", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_users_as_operator(self, client, operator_headers):
        """Test listing users as operator"""
        response = client.get("/api/users/", headers=operator_headers)
        assert response.status_code == 200

    def test_list_users_unauthenticated(self, client):
        """Test listing users without authentication"""
        response = client.get("/api/users/")
        assert response.status_code == 401

    def test_list_users_pagination(self, client, admin_headers):
        """Test listing users with pagination"""
        response = client.get("/api/users/?skip=0&limit=10", headers=admin_headers)
        assert response.status_code == 200
        assert len(response.json()) <= 10


class TestCreateUser:
    """Test POST /api/users/"""

    def test_create_user_success(self, client, admin_headers):
        """Test creating a new user"""
        response = client.post(
            "/api/users/",
            headers=admin_headers,
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "password123",
                "role": "operator"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "newuser"

    def test_create_user_duplicate_username(self, client, admin_headers, admin_user):
        """Test creating user with duplicate username"""
        response = client.post(
            "/api/users/",
            headers=admin_headers,
            json={
                "username": "admin",  # Already exists
                "email": "another@example.com",
                "password": "password123"
            }
        )
        assert response.status_code == 400

    def test_create_user_duplicate_email(self, client, admin_headers, admin_user):
        """Test creating user with duplicate email"""
        response = client.post(
            "/api/users/",
            headers=admin_headers,
            json={
                "username": "anotheruser",
                "email": "admin@example.com",  # Already exists
                "password": "password123"
            }
        )
        assert response.status_code == 400

    def test_create_user_missing_fields(self, client, admin_headers):
        """Test creating user with missing required fields"""
        response = client.post(
            "/api/users/",
            headers=admin_headers,
            json={"username": "newuser"}
        )
        assert response.status_code == 422

    def test_create_user_viewer_forbidden(self, client, viewer_headers):
        """Test viewer cannot create users"""
        response = client.post(
            "/api/users/",
            headers=viewer_headers,
            json={
                "username": "newuser",
                "password": "password123"
            }
        )
        assert response.status_code == 403


class TestGetUser:
    """Test GET /api/users/{user_id}"""

    def test_get_user_by_id(self, client, admin_headers, admin_user):
        """Test getting user by ID"""
        response = client.get(f"/api/users/{admin_user.id}", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == admin_user.id

    def test_get_nonexistent_user(self, client, admin_headers):
        """Test getting non-existent user"""
        response = client.get("/api/users/99999", headers=admin_headers)
        assert response.status_code == 404


class TestUpdateUser:
    """Test PUT /api/users/{user_id}"""

    def test_update_user_success(self, client, admin_headers, operator_user):
        """Test updating user info"""
        response = client.put(
            f"/api/users/{operator_user.id}",
            headers=admin_headers,
            json={"full_name": "Updated Name"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Updated Name"

    def test_update_nonexistent_user(self, client, admin_headers):
        """Test updating non-existent user"""
        response = client.put(
            "/api/users/99999",
            headers=admin_headers,
            json={"full_name": "New Name"}
        )
        assert response.status_code == 404

    def test_update_user_forbidden(self, client, viewer_headers, operator_user):
        """Test viewer cannot update users"""
        response = client.put(
            f"/api/users/{operator_user.id}",
            headers=viewer_headers,
            json={"full_name": "Hacked Name"}
        )
        assert response.status_code == 403


class TestDeleteUser:
    """Test DELETE /api/users/{user_id}"""

    def test_delete_user_success(self, client, admin_headers, operator_user):
        """Test deleting a user"""
        response = client.delete(
            f"/api/users/{operator_user.id}",
            headers=admin_headers
        )
        assert response.status_code == 200

    def test_delete_nonexistent_user(self, client, admin_headers):
        """Test deleting non-existent user"""
        response = client.delete("/api/users/99999", headers=admin_headers)
        assert response.status_code == 404

    def test_delete_user_forbidden(self, client, viewer_headers):
        """Test viewer cannot delete users"""
        response = client.delete("/api/users/1", headers=viewer_headers)
        assert response.status_code == 403


class TestUpdateUserRole:
    """Test PUT /api/users/{user_id}/role"""

    def test_update_user_role_success(self, client, admin_headers, operator_user):
        """Test updating user role"""
        response = client.put(
            f"/api/users/{operator_user.id}/role",
            headers=admin_headers,
            json={"role": "viewer"}
        )
        assert response.status_code == 200

    def test_update_user_role_forbidden(self, client, viewer_headers, operator_user):
        """Test non-admin cannot update roles"""
        response = client.put(
            f"/api/users/{operator_user.id}/role",
            headers=viewer_headers,
            json={"role": "admin"}
        )
        assert response.status_code == 403


class TestUpdateUserStatus:
    """Test PUT /api/users/{user_id}/status"""

    def test_update_user_status_success(self, client, admin_headers, operator_user):
        """Test updating user status"""
        response = client.put(
            f"/api/users/{operator_user.id}/status",
            headers=admin_headers,
            json={"status": "inactive"}
        )
        assert response.status_code == 200

    def test_update_own_status_forbidden(self, client, admin_headers, admin_user):
        """Test admin cannot deactivate own account"""
        response = client.put(
            f"/api/users/{admin_user.id}/status",
            headers=admin_headers,
            json={"status": "inactive"}
        )
        assert response.status_code in [400, 403]
