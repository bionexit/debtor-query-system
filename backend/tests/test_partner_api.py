"""
Test cases for Partner API
"""
import pytest
import hmac
import hashlib
import time
from app.models.models import Partner, Debtor, DebtorStatus


def generate_signature(api_key: str, timestamp: int, secret_key: str) -> str:
    """Generate HMAC-SHA256 signature"""
    message = f"{api_key}{timestamp}"
    return hmac.new(
        secret_key.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()


class TestPartnerHealth:
    """Test partner health endpoint"""

    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/api/partner/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"


class TestPartnerQuery:
    """Test partner query endpoint"""

    def test_query_success(self, client, sample_partner, sample_debtor):
        """Test successful debtor query"""
        timestamp = int(time.time())
        signature = generate_signature(
            sample_partner.api_key,
            timestamp,
            sample_partner.secret_key
        )
        
        response = client.post(
            "/api/partner/query",
            headers={
                "Authorization": f"Partner {sample_partner.api_key}:{signature}:{timestamp}"
            },
            json={
                "id_card": sample_debtor.id_card,
                "name": sample_debtor.name
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["debtor_id"] == sample_debtor.id

    def test_query_name_mismatch(self, client, sample_partner, sample_debtor):
        """Test query with name mismatch"""
        timestamp = int(time.time())
        signature = generate_signature(
            sample_partner.api_key,
            timestamp,
            sample_partner.secret_key
        )
        
        response = client.post(
            "/api/partner/query",
            headers={
                "Authorization": f"Partner {sample_partner.api_key}:{signature}:{timestamp}"
            },
            json={
                "id_card": sample_debtor.id_card,
                "name": "Wrong Name"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 403
        assert "does not match" in data["message"].lower()

    def test_query_not_found(self, client, sample_partner):
        """Test query with no matching debtor"""
        timestamp = int(time.time())
        signature = generate_signature(
            sample_partner.api_key,
            timestamp,
            sample_partner.secret_key
        )
        
        response = client.post(
            "/api/partner/query",
            headers={
                "Authorization": f"Partner {sample_partner.api_key}:{signature}:{timestamp}"
            },
            json={
                "id_card": "000000000000000000",
                "name": "Unknown"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 404

    def test_query_invalid_api_key(self, client, sample_partner, sample_debtor):
        """Test query with invalid API key"""
        timestamp = int(time.time())
        signature = generate_signature(
            "invalid_api_key",
            timestamp,
            sample_partner.secret_key
        )
        
        response = client.post(
            "/api/partner/query",
            headers={
                "Authorization": f"Partner invalid_api_key:{signature}:{timestamp}"
            },
            json={
                "id_card": sample_debtor.id_card,
                "name": sample_debtor.name
            }
        )
        assert response.status_code == 401

    def test_query_invalid_signature(self, client, sample_partner, sample_debtor):
        """Test query with invalid signature"""
        timestamp = int(time.time())
        
        response = client.post(
            "/api/partner/query",
            headers={
                "Authorization": f"Partner {sample_partner.api_key}:invalid_signature:{timestamp}"
            },
            json={
                "id_card": sample_debtor.id_card,
                "name": sample_debtor.name
            }
        )
        assert response.status_code == 401

    def test_query_expired_timestamp(self, client, sample_partner, sample_debtor):
        """Test query with expired timestamp (>5 minutes)"""
        timestamp = int(time.time()) - 400  # 6+ minutes ago
        signature = generate_signature(
            sample_partner.api_key,
            timestamp,
            sample_partner.secret_key
        )
        
        response = client.post(
            "/api/partner/query",
            headers={
                "Authorization": f"Partner {sample_partner.api_key}:{signature}:{timestamp}"
            },
            json={
                "id_card": sample_debtor.id_card,
                "name": sample_debtor.name
            }
        )
        assert response.status_code == 401
        assert "expired" in response.json()["detail"].lower()

    def test_query_missing_auth_header(self, client):
        """Test query without authorization header"""
        response = client.post(
            "/api/partner/query",
            json={
                "id_card": "110101199001011234",
                "name": "Test"
            }
        )
        assert response.status_code == 401


class TestPartnerManagement:
    """Test partner management endpoints"""

    def test_create_partner(self, client):
        """Test creating a new partner"""
        response = client.post(
            "/api/partner/partners",
            params={
                "name": "New Partner",
                "rate_limit": 200,
                "daily_limit": 20000
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["partner_name"] == "New Partner"
        assert "api_key" in data
        assert "secret_key" in data

    def test_revoke_partner(self, client, sample_partner):
        """Test revoking a partner"""
        timestamp = int(time.time())
        signature = generate_signature(
            sample_partner.api_key,
            timestamp,
            sample_partner.secret_key
        )
        
        response = client.post(
            f"/api/partner/partners/{sample_partner.id}/revoke",
            headers={
                "Authorization": f"Partner {sample_partner.api_key}:{signature}:{timestamp}"
            }
        )
        assert response.status_code == 200
        assert "revoked" in response.json()["message"].lower()

    def test_regenerate_keys(self, client, sample_partner):
        """Test regenerating partner API keys"""
        old_api_key = sample_partner.api_key
        old_secret_key = sample_partner.secret_key
        
        timestamp = int(time.time())
        signature = generate_signature(
            sample_partner.api_key,
            timestamp,
            sample_partner.secret_key
        )
        
        response = client.post(
            f"/api/partner/partners/{sample_partner.id}/regenerate-keys",
            headers={
                "Authorization": f"Partner {sample_partner.api_key}:{signature}:{timestamp}"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["api_key"] != old_api_key
        assert data["secret_key"] != old_secret_key


class TestRateLimiting:
    """Test partner rate limiting"""

    def test_rate_limit_check(self, client, sample_partner, sample_debtor, db_session):
        """Test rate limiting logic"""
        # Set daily limit to 0
        sample_partner.daily_query_limit = 0
        db_session.commit()
        
        timestamp = int(time.time())
        signature = generate_signature(
            sample_partner.api_key,
            timestamp,
            sample_partner.secret_key
        )
        
        response = client.post(
            "/api/partner/query",
            headers={
                "Authorization": f"Partner {sample_partner.api_key}:{signature}:{timestamp}"
            },
            json={
                "id_card": sample_debtor.id_card,
                "name": sample_debtor.name
            }
        )
        assert response.status_code == 429
        assert "limit" in response.json()["detail"].lower()


class TestDailyLimit:
    """Test partner daily limit"""

    def test_daily_limit_exceeded(self, client, sample_partner, sample_debtor, db_session):
        """Test daily limit exceeded"""
        sample_partner.today_query_count = sample_partner.daily_query_limit
        db_session.commit()
        
        timestamp = int(time.time())
        signature = generate_signature(
            sample_partner.api_key,
            timestamp,
            sample_partner.secret_key
        )
        
        response = client.post(
            "/api/partner/query",
            headers={
                "Authorization": f"Partner {sample_partner.api_key}:{signature}:{timestamp}"
            },
            json={
                "id_card": sample_debtor.id_card,
                "name": sample_debtor.name
            }
        )
        assert response.status_code == 429
        assert "daily" in response.json()["detail"].lower()

    def test_usage_incremented(self, client, sample_partner, sample_debtor, db_session):
        """Test usage is incremented after query"""
        initial_usage = sample_partner.today_query_count
        
        timestamp = int(time.time())
        signature = generate_signature(
            sample_partner.api_key,
            timestamp,
            sample_partner.secret_key
        )
        
        response = client.post(
            "/api/partner/query",
            headers={
                "Authorization": f"Partner {sample_partner.api_key}:{signature}:{timestamp}"
            },
            json={
                "id_card": sample_debtor.id_card,
                "name": sample_debtor.name
            }
        )
        assert response.status_code == 200
        
        db_session.refresh(sample_partner)
        assert sample_partner.today_query_count == initial_usage + 1
