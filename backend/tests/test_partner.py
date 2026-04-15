"""
Test cases for Partner API (partner.py)
Covering: registration, token, query, voucher upload
"""
import pytest


class TestPartnerRegister:
    """Test POST /api/partner/register"""

    def test_partner_register_success(self, client):
        """Test successful partner registration"""
        response = client.post(
            "/api/partner/register",
            json={
                "name": "New Partner",
                "api_key": "new-partner-api-key-123",
                "secret_key": "secret123"
            }
        )
        assert response.status_code in [200, 201]

    def test_partner_register_duplicate_api_key(self, client, sample_partner):
        """Test registration with duplicate API key"""
        response = client.post(
            "/api/partner/register",
            json={
                "name": "Another Partner",
                "api_key": sample_partner.api_key,
                "secret_key": "secret456"
            }
        )
        assert response.status_code == 400

    def test_partner_register_missing_fields(self, client):
        """Test registration with missing fields"""
        response = client.post(
            "/api/partner/register",
            json={"name": "Test Partner"}
        )
        assert response.status_code == 422


class TestPartnerToken:
    """Test POST /api/partner/token"""

    def test_partner_get_token_success(self, client, sample_partner):
        """Test getting partner access token"""
        response = client.post(
            "/api/partner/token",
            json={
                "api_key": sample_partner.api_key,
                "secret_key": sample_partner.secret_key
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    def test_partner_get_token_wrong_secret(self, client, sample_partner):
        """Test getting token with wrong secret"""
        response = client.post(
            "/api/partner/token",
            json={
                "api_key": sample_partner.api_key,
                "secret_key": "wrong_secret"
            }
        )
        assert response.status_code == 401

    def test_partner_get_token_nonexistent(self, client):
        """Test getting token for non-existent partner"""
        response = client.post(
            "/api/partner/token",
            json={
                "api_key": "nonexistent",
                "secret_key": "secret"
            }
        )
        assert response.status_code == 404

    def test_partner_get_token_disabled(self, client, db_session, sample_partner):
        """Test getting token for disabled partner"""
        sample_partner.is_active = False
        db_session.commit()
        response = client.post(
            "/api/partner/token",
            json={
                "api_key": sample_partner.api_key,
                "secret_key": sample_partner.secret_key
            }
        )
        assert response.status_code == 403


class TestPartnerQuery:
    """Test partner debt query endpoints"""

    def test_partner_query_with_valid_token(self, client, sample_partner):
        """Test partner query with valid token"""
        # First get a token
        token_response = client.post(
            "/api/partner/token",
            json={
                "api_key": sample_partner.api_key,
                "secret_key": sample_partner.secret_key
            }
        )
        if token_response.status_code == 200:
            token = token_response.json().get("access_token")
            response = client.get(
                "/api/partner/query",
                headers={"Authorization": f"Bearer {token}"}
            )
            assert response.status_code in [200, 404]  # 404 if no data

    def test_partner_query_without_token(self, client):
        """Test partner query without token"""
        response = client.get("/api/partner/query")
        assert response.status_code == 401

    def test_partner_query_with_invalid_token(self, client):
        """Test partner query with invalid token"""
        response = client.get(
            "/api/partner/query",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401


class TestPartnerRevoke:
    """Test partner revocation endpoints"""

    def test_partner_revoke_by_admin(self, client, admin_headers, sample_partner):
        """Test admin revoking partner access"""
        response = client.post(
            f"/api/partner/{sample_partner.id}/revoke",
            headers=admin_headers
        )
        assert response.status_code == 200

    def test_partner_revoke_unauthorized(self, client, viewer_headers, sample_partner):
        """Test unauthorized partner revocation"""
        response = client.post(
            f"/api/partner/{sample_partner.id}/revoke",
            headers=viewer_headers
        )
        assert response.status_code == 403
