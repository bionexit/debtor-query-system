"""
Test cases for Config API
"""
import pytest
from app.models.models import Config, ConfigChangeLog


class TestCreateConfig:
    """Test config creation"""

    def test_create_config_success(self, client, admin_headers):
        """Test successful config creation"""
        response = client.post(
            "/api/configs/",
            headers=admin_headers,
            json={
                "config_key": "NEW_CONFIG",
                "config_value": "new_value",
                "description": "New configuration"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["config_key"] == "NEW_CONFIG"
        assert data["config_value"] == "new_value"
        assert data["is_active"] == True

    def test_create_config_duplicate_key(self, client, admin_headers, sample_config):
        """Test creating config with duplicate key"""
        response = client.post(
            "/api/configs/",
            headers=admin_headers,
            json={
                "config_key": sample_config.config_key,
                "config_value": "value"
            }
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()

    def test_create_config_operator_forbidden(self, client, operator_headers):
        """Test operator cannot create config"""
        response = client.post(
            "/api/configs/",
            headers=operator_headers,
            json={
                "config_key": "FORBIDDEN",
                "config_value": "value"
            }
        )
        assert response.status_code == 403


class TestGetConfig:
    """Test getting config"""

    def test_get_config_by_id(self, client, admin_headers, sample_config):
        """Test getting config by ID"""
        response = client.get(
            f"/api/configs/{sample_config.id}",
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_config.id

    def test_get_config_by_key(self, client, admin_headers, sample_config):
        """Test getting config by key"""
        response = client.get(
            f"/api/configs/key/{sample_config.config_key}",
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["config_key"] == sample_config.config_key

    def test_get_nonexistent_config(self, client, admin_headers):
        """Test getting nonexistent config"""
        response = client.get(
            "/api/configs/99999",
            headers=admin_headers
        )
        assert response.status_code == 404


class TestListConfigs:
    """Test listing configs"""

    def test_list_configs(self, client, admin_headers, sample_config):
        """Test listing all configs"""
        response = client.get("/api/configs/", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    def test_list_active_configs(self, client, admin_headers, sample_config):
        """Test listing only active configs"""
        response = client.get(
            "/api/configs/?is_active=true",
            headers=admin_headers
        )
        assert response.status_code == 200
        for config in response.json():
            assert config["is_active"] == True


class TestUpdateConfig:
    """Test updating config"""

    def test_update_config_success(self, client, admin_headers, sample_config):
        """Test successful config update"""
        response = client.put(
            f"/api/configs/{sample_config.id}",
            headers=admin_headers,
            json={
                "config_value": "updated_value",
                "description": "Updated description"
            },
            params={"change_reason": "Testing update"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["config_value"] == "updated_value"

    def test_update_nonexistent_config(self, client, admin_headers):
        """Test updating nonexistent config"""
        response = client.put(
            "/api/configs/99999",
            headers=admin_headers,
            json={"config_value": "new_value"}
        )
        assert response.status_code == 400

    def test_update_config_creates_log(self, client, admin_headers, sample_config, db_session):
        """Test that updating config creates change log"""
        response = client.put(
            f"/api/configs/{sample_config.id}",
            headers=admin_headers,
            json={"config_value": "logged_value"},
            params={"change_reason": "Creating log"}
        )
        assert response.status_code == 200
        
        # Check change log was created
        logs = db_session.query(ConfigChangeLog).filter(
            ConfigChangeLog.config_id == sample_config.id
        ).all()
        
        assert len(logs) >= 1
        assert logs[-1].old_value == sample_config.config_value
        assert logs[-1].new_value == "logged_value"

    def test_update_config_operator_forbidden(self, client, operator_headers, sample_config):
        """Test operator cannot update config"""
        response = client.put(
            f"/api/configs/{sample_config.id}",
            headers=operator_headers,
            json={"config_value": "new_value"}
        )
        assert response.status_code == 403


class TestSwitchConfig:
    """Test quick config switching"""

    def test_switch_config_success(self, client, admin_headers, sample_config):
        """Test successful config switch"""
        response = client.post(
            f"/api/configs/switch/{sample_config.config_key}",
            headers=admin_headers,
            params={
                "new_value": "switched_value",
                "reason": "Quick switch"
            }
        )
        assert response.status_code == 200
        assert "switched" in response.json()["message"].lower()

    def test_switch_nonexistent_config(self, client, admin_headers):
        """Test switching nonexistent config"""
        response = client.post(
            "/api/configs/switch/NONEXISTENT",
            headers=admin_headers,
            params={"new_value": "value"}
        )
        assert response.status_code == 404

    def test_switch_inactive_config(self, client, admin_headers, sample_config, db_session):
        """Test switching inactive config"""
        sample_config.is_active = False
        db_session.commit()
        
        response = client.post(
            f"/api/configs/switch/{sample_config.config_key}",
            headers=admin_headers,
            params={"new_value": "value"}
        )
        assert response.status_code == 404


class TestDeleteConfig:
    """Test config deletion (soft delete)"""

    def test_delete_config_success(self, client, admin_headers, sample_config):
        """Test successful config deletion (soft delete)"""
        response = client.delete(
            f"/api/configs/{sample_config.id}",
            headers=admin_headers
        )
        assert response.status_code == 200
        
        # Verify config is deactivated
        from app.services.config_service import ConfigService
        config = ConfigService.get_config(db_session, sample_config.id)
        assert config.is_active == False

    def test_delete_nonexistent_config(self, client, admin_headers):
        """Test deleting nonexistent config"""
        response = client.delete(
            "/api/configs/99999",
            headers=admin_headers
        )
        assert response.status_code == 400

    def test_delete_config_operator_forbidden(self, client, operator_headers, sample_config):
        """Test operator cannot delete config"""
        response = client.delete(
            f"/api/configs/{sample_config.id}",
            headers=operator_headers
        )
        assert response.status_code == 403


class TestConfigChangeLogs:
    """Test config change log endpoints"""

    def test_get_config_logs(self, client, admin_headers, sample_config, db_session):
        """Test getting config change logs"""
        # Create some change logs first
        for i in range(3):
            log = ConfigChangeLog(
                config_id=sample_config.id,
                old_value=f"old_{i}",
                new_value=f"new_{i}",
                change_reason=f"Test {i}"
            )
            db_session.add(log)
        db_session.commit()
        
        response = client.get(
            f"/api/configs/{sample_config.id}/logs",
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3

    def test_get_all_logs_admin_only(self, client, operator_headers):
        """Test getting all logs requires admin"""
        response = client.get(
            "/api/configs/logs/all",
            headers=operator_headers
        )
        assert response.status_code == 403
