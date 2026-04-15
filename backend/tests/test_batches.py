"""
Test cases for Batches API
"""
import pytest
from app.models.models import Batch, BatchStatus


class TestCreateBatch:
    """Test batch creation"""

    def test_create_batch_success(self, client, operator_headers):
        """Test successful batch creation"""
        response = client.post(
            "/api/batches/",
            headers=operator_headers,
            json={
                "name": "New Batch",
                "description": "Test batch"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Batch"
        assert data["status"] == "pending"
        assert "batch_no" in data

    def test_create_batch_without_description(self, client, operator_headers):
        """Test creating batch without description"""
        response = client.post(
            "/api/batches/",
            headers=operator_headers,
            json={"name": "Simple Batch"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Simple Batch"

    def test_create_batch_viewer_forbidden(self, client, viewer_headers):
        """Test viewer cannot create batch"""
        response = client.post(
            "/api/batches/",
            headers=viewer_headers,
            json={"name": "Forbidden Batch"}
        )
        assert response.status_code == 403


class TestGetBatch:
    """Test getting batch"""

    def test_get_batch_success(self, client, admin_headers, sample_batch):
        """Test getting batch by ID"""
        response = client.get(
            f"/api/batches/{sample_batch.id}",
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_batch.id
        assert data["name"] == sample_batch.name

    def test_get_nonexistent_batch(self, client, admin_headers):
        """Test getting nonexistent batch"""
        response = client.get(
            "/api/batches/99999",
            headers=admin_headers
        )
        assert response.status_code == 404


class TestListBatches:
    """Test listing batches"""

    def test_list_batches(self, client, admin_headers, sample_batch):
        """Test listing all batches"""
        response = client.get("/api/batches/", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    def test_list_batches_with_status_filter(self, client, admin_headers, sample_batch):
        """Test listing batches with status filter"""
        response = client.get(
            "/api/batches/?status=pending",
            headers=admin_headers
        )
        assert response.status_code == 200
        for batch in response.json():
            assert batch["status"] == "pending"

    def test_list_batches_with_creator_filter(self, client, admin_headers, admin_user):
        """Test listing batches created by specific user"""
        response = client.get(
            f"/api/batches/?created_by={admin_user.id}",
            headers=admin_headers
        )
        assert response.status_code == 200

    def test_list_batches_pagination(self, client, admin_headers):
        """Test listing batches with pagination"""
        response = client.get(
            "/api/batches/?skip=0&limit=2",
            headers=admin_headers
        )
        assert response.status_code == 200
        assert len(response.json()) <= 2


class TestUpdateBatch:
    """Test updating batch"""

    def test_update_batch_success(self, client, operator_headers, sample_batch):
        """Test successful batch update"""
        response = client.put(
            f"/api/batches/{sample_batch.id}",
            headers=operator_headers,
            json={
                "name": "Updated Batch Name",
                "description": "Updated description"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Batch Name"

    def test_update_batch_status(self, client, operator_headers, sample_batch):
        """Test updating batch status"""
        response = client.put(
            f"/api/batches/{sample_batch.id}",
            headers=operator_headers,
            json={"status": "processing"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processing"

    def test_update_completed_batch_forbidden(self, client, operator_headers, db_session, admin_user):
        """Test cannot update completed batch"""
        batch = Batch(
            batch_no="BATCH-COMPLETED",
            name="Completed Batch",
            status=BatchStatus.COMPLETED,
            created_by=admin_user.id
        )
        db_session.add(batch)
        db_session.commit()
        
        response = client.put(
            f"/api/batches/{batch.id}",
            headers=operator_headers,
            json={"name": "New Name"}
        )
        assert response.status_code == 400
        assert "cannot update" in response.json()["detail"].lower()

    def test_update_nonexistent_batch(self, client, operator_headers):
        """Test updating nonexistent batch"""
        response = client.put(
            "/api/batches/99999",
            headers=operator_headers,
            json={"name": "New Name"}
        )
        assert response.status_code == 400


class TestDeleteBatch:
    """Test deleting batch"""

    def test_delete_batch_success(self, client, operator_headers, sample_batch):
        """Test successful batch deletion"""
        response = client.delete(
            f"/api/batches/{sample_batch.id}",
            headers=operator_headers
        )
        assert response.status_code == 200
        
        # Verify deletion
        response = client.get(
            f"/api/batches/{sample_batch.id}",
            headers=operator_headers
        )
        assert response.status_code == 404

    def test_delete_processing_batch_forbidden(self, client, operator_headers, db_session, admin_user):
        """Test cannot delete processing batch"""
        batch = Batch(
            batch_no="BATCH-PROCESSING",
            name="Processing Batch",
            status=BatchStatus.PROCESSING,
            created_by=admin_user.id
        )
        db_session.add(batch)
        db_session.commit()
        
        response = client.delete(
            f"/api/batches/{batch.id}",
            headers=operator_headers
        )
        assert response.status_code == 400
        assert "processing" in response.json()["detail"].lower()

    def test_delete_nonexistent_batch(self, client, operator_headers):
        """Test deleting nonexistent batch"""
        response = client.delete(
            "/api/batches/99999",
            headers=operator_headers
        )
        assert response.status_code == 400

    def test_delete_batch_viewer_forbidden(self, client, viewer_headers, sample_batch):
        """Test viewer cannot delete batch"""
        response = client.delete(
            f"/api/batches/{sample_batch.id}",
            headers=viewer_headers
        )
        assert response.status_code == 403
