"""
Test cases for Vouchers API
"""
import pytest
import io
from app.models.models import Voucher, VoucherStatus


class TestUploadVoucher:
    """Test voucher upload"""

    def test_upload_voucher_success(self, client, operator_headers):
        """Test successful voucher upload"""
        # Create a fake Excel file
        file_content = b"Name,ID Card,Phone\nTest,110101199001011234,13800138000"
        file = io.BytesIO(file_content)
        file.name = "test.xlsx"
        
        response = client.post(
            "/api/vouchers/upload",
            headers=operator_headers,
            files={"file": ("test.xlsx", file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["file_name"] == "test.xlsx"
        assert data["status"] == "pending"

    def test_upload_voucher_invalid_type(self, client, operator_headers):
        """Test upload with invalid file type"""
        file_content = b"Not an Excel file"
        file = io.BytesIO(file_content)
        file.name = "test.txt"
        
        response = client.post(
            "/api/vouchers/upload",
            headers=operator_headers,
            files={"file": ("test.txt", file, "text/plain")}
        )
        assert response.status_code == 400
        assert "excel" in response.json()["detail"].lower()

    def test_upload_voucher_viewer_forbidden(self, client, viewer_headers):
        """Test viewer cannot upload voucher"""
        file_content = b"Name,ID Card,Phone\nTest,110101199001011234,13800138000"
        file = io.BytesIO(file_content)
        file.name = "test.xlsx"
        
        response = client.post(
            "/api/vouchers/upload",
            headers=viewer_headers,
            files={"file": ("test.xlsx", file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        )
        assert response.status_code == 403


class TestGetVoucher:
    """Test getting voucher"""

    def test_get_voucher_success(self, client, admin_headers, sample_voucher):
        """Test getting voucher by ID"""
        response = client.get(
            f"/api/vouchers/{sample_voucher.id}",
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_voucher.id

    def test_get_nonexistent_voucher(self, client, admin_headers):
        """Test getting nonexistent voucher"""
        response = client.get(
            "/api/vouchers/99999",
            headers=admin_headers
        )
        assert response.status_code == 404


class TestListVouchers:
    """Test listing vouchers"""

    def test_list_vouchers(self, client, admin_headers, sample_voucher):
        """Test listing all vouchers"""
        response = client.get("/api/vouchers/", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    def test_list_vouchers_with_status_filter(self, client, admin_headers, sample_voucher):
        """Test listing vouchers with status filter"""
        response = client.get(
            "/api/vouchers/?status=pending",
            headers=admin_headers
        )
        assert response.status_code == 200
        for voucher in response.json():
            assert voucher["status"] == "pending"


class TestApproveVoucher:
    """Test approving voucher"""

    def test_approve_voucher_success(self, client, admin_headers, sample_voucher):
        """Test successful voucher approval"""
        response = client.post(
            f"/api/vouchers/{sample_voucher.id}/approve",
            headers=admin_headers,
            json={"comment": "Approved for import"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Voucher approved successfully"

    def test_approve_voucher_with_no_comment(self, client, admin_headers, sample_voucher):
        """Test approving voucher without comment"""
        response = client.post(
            f"/api/vouchers/{sample_voucher.id}/approve",
            headers=admin_headers
        )
        assert response.status_code == 200

    def test_approve_already_approved_voucher(self, client, admin_headers, sample_voucher, db_session):
        """Test approving already approved voucher"""
        sample_voucher.status = VoucherStatus.APPROVED
        db_session.commit()
        
        response = client.post(
            f"/api/vouchers/{sample_voucher.id}/approve",
            headers=admin_headers
        )
        assert response.status_code == 400

    def test_approve_voucher_operator_forbidden(self, client, operator_headers, sample_voucher):
        """Test operator cannot approve voucher"""
        response = client.post(
            f"/api/vouchers/{sample_voucher.id}/approve",
            headers=operator_headers
        )
        assert response.status_code == 403


class TestRejectVoucher:
    """Test rejecting voucher"""

    def test_reject_voucher_success(self, client, admin_headers, sample_voucher):
        """Test successful voucher rejection"""
        response = client.post(
            f"/api/vouchers/{sample_voucher.id}/reject",
            headers=admin_headers,
            json={"comment": "Invalid data format"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "rejected" in data["message"].lower()

    def test_reject_already_rejected_voucher(self, client, admin_headers, sample_voucher, db_session):
        """Test rejecting already rejected voucher"""
        sample_voucher.status = VoucherStatus.REJECTED
        db_session.commit()
        
        response = client.post(
            f"/api/vouchers/{sample_voucher.id}/reject",
            headers=admin_headers
        )
        assert response.status_code == 400

    def test_reject_voucher_operator_forbidden(self, client, operator_headers, sample_voucher):
        """Test operator cannot reject voucher"""
        response = client.post(
            f"/api/vouchers/{sample_voucher.id}/reject",
            headers=operator_headers
        )
        assert response.status_code == 403


class TestDeleteVoucher:
    """Test deleting voucher"""

    def test_delete_voucher_success(self, client, admin_headers, sample_voucher):
        """Test successful voucher deletion"""
        response = client.delete(
            f"/api/vouchers/{sample_voucher.id}",
            headers=admin_headers
        )
        assert response.status_code == 200

    def test_delete_nonexistent_voucher(self, client, admin_headers):
        """Test deleting nonexistent voucher"""
        response = client.delete(
            "/api/vouchers/99999",
            headers=admin_headers
        )
        assert response.status_code == 400

    def test_delete_voucher_operator_forbidden(self, client, operator_headers, sample_voucher):
        """Test operator cannot delete voucher"""
        response = client.delete(
            f"/api/vouchers/{sample_voucher.id}",
            headers=operator_headers
        )
        assert response.status_code == 403
