"""
Test cases for Debtors API
"""
import pytest
from app.models.models import Debtor, DebtorStatus, Batch, BatchStatus


class TestCreateDebtor:
    """Test debtor creation"""

    def test_create_debtor_success(self, client, operator_headers, sample_batch):
        """Test successful debtor creation"""
        response = client.post(
            "/api/debtors/",
            headers=operator_headers,
            json={
                "name": "Li Si",
                "id_card": "110101199501011234",
                "phone": "13900139001",
                "address": "Shanghai",
                "debt_amount": 50000.0,
                "batch_id": sample_batch.id
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Li Si"
        assert data["id_card"] == "110101199501011234"
        assert data["status"] == "active"

    def test_create_debtor_duplicate_id_card(self, client, operator_headers, sample_debtor):
        """Test creating debtor with duplicate ID card"""
        response = client.post(
            "/api/debtors/",
            headers=operator_headers,
            json={
                "name": "Another Person",
                "id_card": sample_debtor.id_card,  # Same ID card
                "phone": "13900139002"
            }
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()

    def test_create_debtor_invalid_batch(self, client, operator_headers):
        """Test creating debtor with invalid batch"""
        response = client.post(
            "/api/debtors/",
            headers=operator_headers,
            json={
                "name": "Li Si",
                "id_card": "110101199501011235",
                "phone": "13900139003",
                "batch_id": 99999  # Non-existent batch
            }
        )
        assert response.status_code == 400
        assert "batch" in response.json()["detail"].lower()

    def test_create_debtor_viewer_forbidden(self, client, viewer_headers, sample_batch):
        """Test viewer cannot create debtor"""
        response = client.post(
            "/api/debtors/",
            headers=viewer_headers,
            json={
                "name": "Li Si",
                "id_card": "110101199501011236",
                "phone": "13900139004"
            }
        )
        assert response.status_code == 403


class TestGetDebtor:
    """Test getting debtor"""

    def test_get_debtor_success(self, client, admin_headers, sample_debtor):
        """Test getting debtor by ID"""
        response = client.get(
            f"/api/debtors/{sample_debtor.id}",
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_debtor.id
        assert data["name"] == sample_debtor.name

    def test_get_nonexistent_debtor(self, client, admin_headers):
        """Test getting nonexistent debtor"""
        response = client.get(
            "/api/debtors/99999",
            headers=admin_headers
        )
        assert response.status_code == 404


class TestListDebtors:
    """Test listing debtors"""

    def test_list_debtors(self, client, admin_headers, sample_debtors):
        """Test listing all debtors"""
        response = client.get("/api/debtors/", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 5

    def test_list_debtors_with_status_filter(self, client, admin_headers, sample_debtors):
        """Test listing debtors with status filter"""
        response = client.get(
            "/api/debtors/?status=active",
            headers=admin_headers
        )
        assert response.status_code == 200
        for debtor in response.json():
            assert debtor["status"] == "active"

    def test_list_debtors_with_batch_filter(self, client, admin_headers, sample_batch, sample_debtors):
        """Test listing debtors with batch filter"""
        response = client.get(
            f"/api/debtors/?batch_id={sample_batch.id}",
            headers=admin_headers
        )
        assert response.status_code == 200
        for debtor in response.json():
            assert debtor["batch_id"] == sample_batch.id

    def test_list_debtors_pagination(self, client, admin_headers, sample_debtors):
        """Test listing debtors with pagination"""
        response = client.get(
            "/api/debtors/?skip=0&limit=2",
            headers=admin_headers
        )
        assert response.status_code == 200
        assert len(response.json()) <= 2


class TestUpdateDebtor:
    """Test updating debtor"""

    def test_update_debtor_success(self, client, operator_headers, sample_debtor):
        """Test successful debtor update"""
        response = client.put(
            f"/api/debtors/{sample_debtor.id}",
            headers=operator_headers,
            json={
                "name": "Updated Name",
                "debt_amount": 20000.0,
                "status": "blacklisted"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["debt_amount"] == 20000.0
        assert data["status"] == "blacklisted"

    def test_update_nonexistent_debtor(self, client, operator_headers):
        """Test updating nonexistent debtor"""
        response = client.put(
            "/api/debtors/99999",
            headers=operator_headers,
            json={"name": "New Name"}
        )
        assert response.status_code == 400

    def test_update_debtor_duplicate_id_card(self, client, operator_headers, sample_debtors):
        """Test updating debtor with duplicate ID card"""
        # Get a debtor to update
        response = client.get("/api/debtors/", headers=operator_headers)
        debtors = response.json()
        target = debtors[0]
        other = debtors[1]
        
        response = client.put(
            f"/api/debtors/{target['id']}",
            headers=operator_headers,
            json={"id_card": other["id_card"]}
        )
        assert response.status_code == 400


class TestDeleteDebtor:
    """Test deleting debtor"""

    def test_delete_debtor_success(self, client, operator_headers, sample_debtor):
        """Test successful debtor deletion"""
        response = client.delete(
            f"/api/debtors/{sample_debtor.id}",
            headers=operator_headers
        )
        assert response.status_code == 200
        
        # Verify deletion
        response = client.get(
            f"/api/debtors/{sample_debtor.id}",
            headers=operator_headers
        )
        assert response.status_code == 404

    def test_delete_nonexistent_debtor(self, client, operator_headers):
        """Test deleting nonexistent debtor"""
        response = client.delete(
            "/api/debtors/99999",
            headers=operator_headers
        )
        assert response.status_code == 400

    def test_delete_debtor_viewer_forbidden(self, client, viewer_headers, sample_debtor):
        """Test viewer cannot delete debtor"""
        response = client.delete(
            f"/api/debtors/{sample_debtor.id}",
            headers=viewer_headers
        )
        assert response.status_code == 403


class TestSearchDebtors:
    """Test searching debtors"""

    def test_search_by_name(self, client, admin_headers, sample_debtors):
        """Test searching by name"""
        response = client.get(
            "/api/debtors/search/?keyword=Debtor",
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["debtors"]) > 0

    def test_search_by_id_card(self, client, admin_headers, sample_debtor):
        """Test searching by ID card"""
        response = client.get(
            f"/api/debtors/search/?keyword={sample_debtor.id_card[:6]}",
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["debtors"]) > 0

    def test_search_by_phone(self, client, admin_headers, sample_debtor):
        """Test searching by phone"""
        response = client.get(
            f"/api/debtors/search/?keyword={sample_debtor.phone[:6]}",
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["debtors"]) > 0

    def test_search_empty_keyword(self, client, admin_headers):
        """Test search with empty keyword"""
        response = client.get(
            "/api/debtors/search/?keyword=",
            headers=admin_headers
        )
        assert response.status_code == 422
