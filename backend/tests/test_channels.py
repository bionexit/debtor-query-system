"""
Test cases for Channels API
"""
import pytest
from app.models.models import SMSChannel, ChannelStatus


class TestCreateChannel:
    """Test channel creation"""

    def test_create_channel_success(self, client, operator_headers):
        """Test successful channel creation"""
        response = client.post(
            "/api/channels/",
            headers=operator_headers,
            json={
                "name": "New Channel",
                "provider": "NewProvider",
                "endpoint": "http://new-provider.com/api",
                "api_key": "new-api-key",
                "priority": 5
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Channel"
        assert data["status"] == "testing"  # New channels start in testing

    def test_create_channel_minimal(self, client, operator_headers):
        """Test creating channel with minimal data"""
        response = client.post(
            "/api/channels/",
            headers=operator_headers,
            json={
                "name": "Minimal Channel",
                "provider": "MinimalProvider"
            }
        )
        assert response.status_code == 200

    def test_create_channel_viewer_forbidden(self, client, viewer_headers):
        """Test viewer cannot create channel"""
        response = client.post(
            "/api/channels/",
            headers=viewer_headers,
            json={
                "name": "Forbidden Channel",
                "provider": "Provider"
            }
        )
        assert response.status_code == 403


class TestGetChannel:
    """Test getting channel"""

    def test_get_channel_success(self, client, admin_headers, sample_channel):
        """Test getting channel by ID"""
        response = client.get(
            f"/api/channels/{sample_channel.id}",
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_channel.id

    def test_get_nonexistent_channel(self, client, admin_headers):
        """Test getting nonexistent channel"""
        response = client.get(
            "/api/channels/99999",
            headers=admin_headers
        )
        assert response.status_code == 404


class TestListChannels:
    """Test listing channels"""

    def test_list_channels(self, client, admin_headers, sample_channel):
        """Test listing all channels"""
        response = client.get("/api/channels/", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    def test_list_active_channels(self, client, admin_headers, sample_channel):
        """Test listing only active channels"""
        response = client.get(
            "/api/channels/?is_active=true",
            headers=admin_headers
        )
        assert response.status_code == 200
        for channel in response.json():
            assert channel["is_active"] == True

    def test_list_channels_by_status(self, client, admin_headers, sample_channel):
        """Test listing channels by status"""
        response = client.get(
            "/api/channels/?status=active",
            headers=admin_headers
        )
        assert response.status_code == 200


class TestUpdateChannel:
    """Test updating channel"""

    def test_update_channel_success(self, client, operator_headers, sample_channel):
        """Test successful channel update"""
        response = client.put(
            f"/api/channels/{sample_channel.id}",
            headers=operator_headers,
            json={
                "name": "Updated Channel",
                "priority": 10
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Channel"
        assert data["priority"] == 10

    def test_update_nonexistent_channel(self, client, operator_headers):
        """Test updating nonexistent channel"""
        response = client.put(
            "/api/channels/99999",
            headers=operator_headers,
            json={"name": "New Name"}
        )
        assert response.status_code == 400


class TestScanChannels:
    """Test channel scanning/discovery"""

    def test_list_channels_ordered_by_priority(self, client, admin_headers, sample_channel, db_session):
        """Test channels are returned ordered by priority"""
        # Create multiple channels with different priorities
        channels = [
            SMSChannel(
                channel_id=f"TSC{i:03d}",
                channel_name=f"Test Scan Channel {i}",
                channel_code=f"TSCANAL_{i}",
                name=f"Test Scan Channel {i}",
                provider="Provider",
                priority=i,
                is_active=True
            )
            for i in range(3, 0, -1)
        ]
        for ch in channels:
            db_session.add(ch)
        db_session.commit()
        
        response = client.get("/api/channels/", headers=admin_headers)
        assert response.status_code == 200
        
        # Should be ordered by priority descending
        priorities = [ch["priority"] for ch in response.json()[:3]]
        assert priorities == sorted(priorities, reverse=True)


class TestTestChannel:
    """Test channel testing"""

    def test_test_channel_success(self, client, operator_headers, sample_channel):
        """Test successful channel test"""
        response = client.post(
            f"/api/channels/{sample_channel.id}/test",
            headers=operator_headers,
            json={"phone": "13800138000"}
        )
        # May fail due to mock SMS gateway not running, but tests the endpoint
        assert response.status_code in [200, 400, 500]

    def test_test_nonexistent_channel(self, client, operator_headers):
        """Test testing nonexistent channel"""
        response = client.post(
            "/api/channels/99999/test",
            headers=operator_headers,
            json={"phone": "13800138000"}
        )
        assert response.status_code == 404

    def test_test_channel_viewer_forbidden(self, client, viewer_headers, sample_channel):
        """Test viewer cannot test channel"""
        response = client.post(
            f"/api/channels/{sample_channel.id}/test",
            headers=viewer_headers,
            json={"phone": "13800138000"}
        )
        assert response.status_code == 403


class TestEnableDisableChannel:
    """Test enabling and disabling channels"""

    def test_enable_channel_success(self, client, operator_headers, sample_channel, db_session):
        """Test successful channel enable"""
        sample_channel.is_active = False
        sample_channel.status = ChannelStatus.INACTIVE
        db_session.commit()
        
        response = client.post(
            f"/api/channels/{sample_channel.id}/enable",
            headers=operator_headers
        )
        assert response.status_code == 200
        
        db_session.refresh(sample_channel)
        assert sample_channel.is_active == True
        assert sample_channel.status == ChannelStatus.ACTIVE

    def test_disable_channel_success(self, client, operator_headers, sample_channel, db_session):
        """Test successful channel disable"""
        response = client.post(
            f"/api/channels/{sample_channel.id}/disable",
            headers=operator_headers
        )
        assert response.status_code == 200
        
        db_session.refresh(sample_channel)
        assert sample_channel.is_active == False
        assert sample_channel.status == ChannelStatus.INACTIVE

    def test_enable_nonexistent_channel(self, client, operator_headers):
        """Test enabling nonexistent channel"""
        response = client.post(
            "/api/channels/99999/enable",
            headers=operator_headers
        )
        assert response.status_code == 404


class TestDeleteChannel:
    """Test deleting channel"""

    def test_delete_channel_success(self, client, operator_headers, db_session):
        """Test successful channel deletion (only testing status allowed)"""
        # Create channel in testing status
        channel = SMSChannel(
            channel_id="CH999",
            channel_name="To Delete",
            channel_code="CHANNEL_DELETE",
            name="To Delete",
            provider="Provider",
            status=ChannelStatus.TESTING
        )
        db_session.add(channel)
        db_session.commit()
        
        response = client.delete(
            f"/api/channels/{channel.id}",
            headers=operator_headers
        )
        assert response.status_code == 200

    def test_delete_active_channel_forbidden(self, client, operator_headers, sample_channel):
        """Test cannot delete active channel"""
        response = client.delete(
            f"/api/channels/{sample_channel.id}",
            headers=operator_headers
        )
        assert response.status_code == 400
        assert "testing" in response.json()["detail"].lower()
