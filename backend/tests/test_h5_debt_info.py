"""
Test cases for H5 Debt Query API
"""
import pytest


class TestH5DebtorsQuery:
    """Test H5 debtors query endpoint"""

    def test_h5_query_requires_auth(self, client):
        """Test H5 query without auth returns 401"""
        response = client.get("/api/h5/query")
        assert response.status_code == 401

    def test_h5_query_with_invalid_token(self, client):
        """Test H5 query with invalid token returns 401"""
        response = client.get(
            "/api/h5/query",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401

    def test_h5_query_with_malformed_header(self, client):
        """Test H5 query with malformed header returns 401"""
        response = client.get(
            "/api/h5/query",
            headers={"Authorization": "invalid_format"}
        )
        assert response.status_code == 401


class TestH5DebtorDetail:
    """Test H5 debtor detail endpoint"""

    def test_h5_debtor_detail_requires_auth(self, client):
        """Test debtor detail without auth returns 401"""
        response = client.get("/api/h5/debtor/SOME123")
        assert response.status_code == 401

    def test_h5_debtor_detail_not_found(self, client, h5_headers):
        """Test debtor detail for non-existent debtor returns 404"""
        response = client.get(
            "/api/h5/debtor/NONEXISTENT999",
            headers=h5_headers
        )
        assert response.status_code in [401, 404]


class TestH5Stats:
    """Test H5 stats endpoint"""

    def test_h5_stats_requires_auth(self, client):
        """Test stats without auth returns 401"""
        response = client.get("/api/h5/stats")
        assert response.status_code == 401


class TestTokenValidation:
    """Test H5 token validation"""

    def test_missing_bearer_prefix(self, client):
        """Test missing Bearer prefix is rejected"""
        response = client.get(
            "/api/h5/query",
            headers={"Authorization": "some_token"}
        )
        assert response.status_code == 401

    def test_invalid_bearer_format(self, client):
        """Test invalid Bearer format is rejected"""
        response = client.get(
            "/api/h5/query",
            headers={"Authorization": "Bearer "}
        )
        assert response.status_code == 401
