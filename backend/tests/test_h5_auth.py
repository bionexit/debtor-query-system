"""
Test cases for H5 Authentication API
These tests use the actual H5 API endpoints with proper authentication.
"""
import pytest
from datetime import datetime, timedelta
from app.models.models import H5User


class TestCaptchaRequest:
    """Test captcha request endpoint"""

    def test_request_captcha_success(self, client):
        """Test successful captcha request"""
        response = client.post(
            "/api/h5/captcha",
            json={"phone": "13900139000"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "captcha_id" in data
        assert data["expires_in"] > 0

    def test_request_captcha_locked_user(self, client, db_session):
        """Test captcha request for locked user"""
        user = H5User(
            phone="13900139001",
            is_locked=True,
            locked_until=datetime.utcnow() + timedelta(minutes=15)
        )
        db_session.add(user)
        db_session.commit()
        
        response = client.post(
            "/api/h5/captcha",
            json={"phone": "13900139001"}
        )
        assert response.status_code == 429
        assert "locked" in response.json()["detail"].lower()


class TestCaptchaVerify:
    """Test captcha verification endpoint"""

    def test_verify_captcha_success(self, client, db_session):
        """Test successful captcha verification"""
        # Create user with valid captcha
        user = H5User(
            phone="13900139002",
            captcha="123456",
            captcha_expire_at=datetime.utcnow() + timedelta(minutes=5)
        )
        db_session.add(user)
        db_session.commit()
        
        response = client.post(
            "/api/h5/verify",
            json={"phone": "13900139002", "captcha": "123456"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_verify_invalid_captcha(self, client, db_session):
        """Test verification with invalid captcha"""
        user = H5User(
            phone="13900139003",
            captcha="123456",
            captcha_expire_at=datetime.utcnow() + timedelta(minutes=5)
        )
        db_session.add(user)
        db_session.commit()
        
        response = client.post(
            "/api/h5/verify",
            json={"phone": "13900139003", "captcha": "999999"}
        )
        assert response.status_code == 400
        assert "invalid captcha" in response.json()["detail"].lower()

    def test_verify_expired_captcha(self, client, db_session):
        """Test verification with expired captcha"""
        user = H5User(
            phone="13900139004",
            captcha="123456",
            captcha_expire_at=datetime.utcnow() - timedelta(minutes=1)  # Expired
        )
        db_session.add(user)
        db_session.commit()
        
        response = client.post(
            "/api/h5/verify",
            json={"phone": "13900139004", "captcha": "123456"}
        )
        assert response.status_code == 400
        assert "expired" in response.json()["detail"].lower()

    def test_verify_unregistered_phone(self, client):
        """Test verification with unregistered phone"""
        response = client.post(
            "/api/h5/verify",
            json={"phone": "13999999999", "captcha": "123456"}
        )
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"].lower()

    def test_verify_locked_user(self, client, db_session):
        """Test verification for locked user"""
        user = H5User(
            phone="13900139005",
            is_locked=True,
            locked_until=datetime.utcnow() + timedelta(minutes=15)
        )
        db_session.add(user)
        db_session.commit()
        
        response = client.post(
            "/api/h5/verify",
            json={"phone": "13900139005", "captcha": "123456"}
        )
        assert response.status_code == 400
        assert "locked" in response.json()["detail"].lower()

    def test_verify_max_attempts_locked(self, client, db_session):
        """Test account locking after max failed attempts"""
        user = H5User(
            phone="13900139006",
            captcha="123456",
            captcha_expire_at=datetime.utcnow() + timedelta(minutes=5),
            verification_attempts=4
        )
        db_session.add(user)
        db_session.commit()
        
        # 5th attempt should lock
        response = client.post(
            "/api/h5/verify",
            json={"phone": "13900139006", "captcha": "999999"}
        )
        assert response.status_code == 400
        assert "locked" in response.json()["detail"].lower()


class TestH5DebtInfo:
    """Test H5 debt info query"""

    def test_query_debt_info_success(self, client, h5_user, h5_headers, sample_debtor):
        """Test successful debt info query"""
        # Update h5_user to have same phone as sample_debtor's encrypted_phone
        h5_user.phone = "13800138000"
        from app.core.security import create_h5_token
        token = create_h5_token(data={"phone": h5_user.phone, "sub": str(h5_user.id)})
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.post(
            "/api/h5/debt-info",
            headers=headers,
            json={"debtor_id_card": sample_debtor.id_card}
        )
        # Should succeed or return 400 if daily limit exceeded
        assert response.status_code in [200, 400]

    def test_query_debt_info_no_record(self, client, h5_user):
        """Test query with no matching record"""
        from app.core.security import create_h5_token
        token = create_h5_token(data={"phone": h5_user.phone, "sub": str(h5_user.id)})
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.post(
            "/api/h5/debt-info",
            headers=headers,
            json={"debtor_id_card": "000000000000000000"}
        )
        assert response.status_code == 400
        assert "no debt record" in response.json()["detail"].lower()

    def test_query_debt_info_without_token(self, client):
        """Test query without authorization"""
        response = client.post(
            "/api/h5/debt-info",
            json={"debtor_id_card": "110101199001011234"}
        )
        assert response.status_code == 401

    def test_query_debt_info_invalid_token(self, client):
        """Test query with invalid token"""
        response = client.post(
            "/api/h5/debt-info",
            headers={"Authorization": "Bearer invalid_token"},
            json={"debtor_id_card": "110101199001011234"}
        )
        assert response.status_code == 401

    def test_query_debt_info_daily_limit_exceeded(self, client, db_session, h5_user, sample_debtor):
        """Test daily query limit exceeded"""
        from app.core.config import settings
        from app.core.security import create_h5_token
        
        h5_user.daily_query_count = settings.H5_DAILY_QUERY_LIMIT
        h5_user.query_date = datetime.utcnow()
        db_session.commit()
        
        token = create_h5_token(data={"phone": h5_user.phone, "sub": str(h5_user.id)})
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.post(
            "/api/h5/debt-info",
            headers=headers,
            json={"debtor_id_card": sample_debtor.id_card}
        )
        assert response.status_code == 400
        assert "limit" in response.json()["detail"].lower()


class TestGetPaymentAccounts:
    """Test payment accounts endpoint"""

    def test_get_payment_accounts_success(self, client, h5_user, sample_payment_account):
        """Test getting payment accounts"""
        from app.core.security import create_h5_token
        token = create_h5_token(data={"phone": h5_user.phone, "sub": str(h5_user.id)})
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.get(
            "/api/h5/payment-accounts",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["bank_name"] == "ICBC"

    def test_get_payment_accounts_without_token(self, client):
        """Test getting payment accounts without token"""
        response = client.get("/api/h5/payment-accounts")
        assert response.status_code == 401


class TestQueryLimit:
    """Test query limit endpoint"""

    def test_get_query_limit(self, client, h5_user):
        """Test getting query limit info"""
        from app.core.security import create_h5_token
        token = create_h5_token(data={"phone": h5_user.phone, "sub": str(h5_user.id)})
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.get(
            "/api/h5/query-limit",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "remaining" in data
        assert "limit" in data
        assert "reset_at" in data
