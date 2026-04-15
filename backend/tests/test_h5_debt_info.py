"""
Test cases for H5 Debt Info API
"""
import pytest
from datetime import datetime, timedelta
from app.models.models import H5User, DebtInfo


class TestDebtInfoQuery:
    """Test debt info query functionality"""

    def test_query_increments_count(self, client, h5_headers, h5_user, sample_debtor, db_session):
        """Test that query increments daily count"""
        initial_count = h5_user.daily_query_count
        last_query = h5_user.last_query_at
        
        response = client.post(
            "/api/h5/debt-info",
            headers=h5_headers,
            json={"debtor_id_card": sample_debtor.id_card}
        )
        assert response.status_code == 200
        
        db_session.refresh(h5_user)
        assert h5_user.daily_query_count == initial_count + 1

    def test_query_records_history(self, client, h5_headers, h5_user, sample_debtor, db_session):
        """Test that query is recorded in history"""
        response = client.post(
            "/api/h5/debt-info",
            headers=h5_headers,
            json={"debtor_id_card": sample_debtor.id_card}
        )
        assert response.status_code == 200
        
        # Check debt info was created
        debt_info = db_session.query(DebtInfo).filter(
            DebtInfo.h5_user_id == h5_user.id,
            DebtInfo.debtor_id == sample_debtor.id
        ).first()
        
        assert debt_info is not None
        assert debt_info.result_code == "0000"


class TestPaymentAccountRetrieval:
    """Test payment account retrieval"""

    def test_inactive_accounts_excluded(self, client, h5_headers, db_session):
        """Test that inactive payment accounts are excluded"""
        from app.models.models import PaymentAccount
        
        # Create inactive account
        inactive = PaymentAccount(
            bank_name="BOC",
            account_no="6222021111111111",
            account_name="Inactive",
            is_active=False
        )
        db_session.add(inactive)
        db_session.commit()
        
        response = client.get(
            "/api/payment-accounts",
            headers=h5_headers
        )
        assert response.status_code == 200
        
        # Inactive account should not be in response
        banks = [acc["bank_name"] for acc in response.json()]
        assert "BOC" not in banks

    def test_multiple_accounts(self, client, h5_headers, db_session):
        """Test multiple payment accounts are returned"""
        from app.models.models import PaymentAccount
        
        # Create multiple accounts
        accounts = [
            PaymentAccount(bank_name="ABC", account_no="111", account_name="A", is_active=True),
            PaymentAccount(bank_name="BCD", account_no="222", account_name="B", is_active=True),
            PaymentAccount(bank_name="CDE", account_no="333", account_name="C", is_active=True),
        ]
        for acc in accounts:
            db_session.add(acc)
        db_session.commit()
        
        response = client.get(
            "/api/payment-accounts",
            headers=h5_headers
        )
        assert response.status_code == 200
        assert len(response.json()) >= 3


class TestTokenValidation:
    """Test H5 token validation"""

    def test_valid_h5_token(self, client, h5_user, sample_debtor):
        """Test valid H5 token works"""
        response = client.post(
            "/api/h5/debt-info",
            headers=h5_headers,
            json={"debtor_id_card": sample_debtor.id_card}
        )
        assert response.status_code == 200

    def test_admin_token_rejected(self, client, admin_token, sample_debtor):
        """Test that admin JWT token is rejected for H5 endpoints"""
        response = client.post(
            "/api/h5/debt-info",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"debtor_id_card": sample_debtor.id_card}
        )
        assert response.status_code == 401
        assert "invalid token type" in response.json()["detail"].lower()

    def test_expired_token(self, client, db_session, sample_debtor):
        """Test expired H5 token is rejected"""
        from app.core.security import create_h5_token
        
        # Create token that's already expired
        expired_token = create_h5_token(
            data={"phone": "13900139000", "sub": "1"},
            expires_delta=timedelta(seconds=-10)  # Already expired
        )
        
        response = client.post(
            "/api/h5/debt-info",
            headers={"Authorization": f"Bearer {expired_token}"},
            json={"debtor_id_card": sample_debtor.id_card}
        )
        assert response.status_code == 401

    def test_missing_bearer_prefix(self, client, sample_debtor):
        """Test missing Bearer prefix is rejected"""
        response = client.post(
            "/api/h5/debt-info",
            headers={"Authorization": "some_token"},
            json={"debtor_id_card": sample_debtor.id_card}
        )
        assert response.status_code == 401
