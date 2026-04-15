"""
Test cases for H5 API (h5.py)
Covering: H5 query, debtor detail, stats
"""
import pytest


class TestH5QueryDebtors:
    """Test GET /api/h5/query"""

    def test_h5_query_with_valid_token(self, client, h5_headers, sample_debtor):
        """Test H5 query with valid token"""
        response = client.get(
            "/api/h5/query",
            headers=h5_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_h5_query_with_name_filter(self, client, h5_headers, sample_debtor):
        """Test H5 query with name filter"""
        response = client.get(
            f"/api/h5/query?name={sample_debtor.name}",
            headers=h5_headers
        )
        assert response.status_code == 200

    def test_h5_query_with_id_card_filter(self, client, h5_headers, sample_debtor):
        """Test H5 query with ID card filter"""
        response = client.get(
            f"/api/h5/query?id_card={sample_debtor.id_card}",
            headers=h5_headers
        )
        assert response.status_code == 200

    def test_h5_query_without_token(self, client):
        """Test H5 query without token"""
        response = client.get("/api/h5/query")
        assert response.status_code == 401

    def test_h5_query_with_invalid_token(self, client):
        """Test H5 query with invalid token"""
        response = client.get(
            "/api/h5/query",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401

    def test_h5_query_pagination(self, client, h5_headers):
        """Test H5 query with pagination"""
        response = client.get(
            "/api/h5/query?page=1&page_size=10",
            headers=h5_headers
        )
        assert response.status_code == 200


class TestH5GetDebtor:
    """Test GET /api/h5/debtor/{debtor_number}"""

    def test_h5_get_debtor_success(self, client, h5_headers, sample_debtor):
        """Test getting H5 debtor detail"""
        response = client.get(
            f"/api/h5/debtor/{sample_debtor.debtor_number}",
            headers=h5_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["debtor_number"] == sample_debtor.debtor_number

    def test_h5_get_nonexistent_debtor(self, client, h5_headers):
        """Test getting non-existent debtor"""
        response = client.get(
            "/api/h5/debtor/NONEXISTENT",
            headers=h5_headers
        )
        assert response.status_code == 404

    def test_h5_get_debtor_without_token(self, client, sample_debtor):
        """Test getting debtor without token"""
        response = client.get(f"/api/h5/debtor/{sample_debtor.debtor_number}")
        assert response.status_code == 401


class TestH5Stats:
    """Test GET /api/h5/stats"""

    def test_h5_get_stats(self, client, h5_headers):
        """Test getting H5 statistics"""
        response = client.get("/api/h5/stats", headers=h5_headers)
        assert response.status_code == 200

    def test_h5_get_stats_unauthenticated(self, client):
        """Test getting stats without authentication"""
        response = client.get("/api/h5/stats")
        assert response.status_code == 401
