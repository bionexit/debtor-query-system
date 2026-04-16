"""
Test cases for SMS API (Templates and Tasks)
"""
import pytest
from app.models.models import SMSTemplate, SMSTask, SMSTaskStatus, SMSChannel, ChannelStatus


class TestSMSTemplates:
    """Test SMS template endpoints"""

    def test_create_template_success(self, client, operator_headers):
        """Test successful template creation"""
        response = client.post(
            "/api/sms/templates/",
            headers=operator_headers,
            json={
                "name": "Payment Reminder",
                "content": "Dear {{name}}, please pay {{amount}} before {{date}}",
                "variables": "name,amount,date"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Payment Reminder"
        assert data["is_active"] == True

    def test_create_template_without_variables(self, client, operator_headers):
        """Test creating template without variables"""
        response = client.post(
            "/api/sms/templates/",
            headers=operator_headers,
            json={
                "name": "Simple Template",
                "content": "This is a simple message"
            }
        )
        assert response.status_code == 201

    def test_get_template_success(self, client, admin_headers, sample_template):
        """Test getting template by ID"""
        response = client.get(
            f"/api/sms/templates/{sample_template.id}",
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_template.id

    def test_get_nonexistent_template(self, client, admin_headers):
        """Test getting nonexistent template"""
        response = client.get(
            "/api/sms/templates/99999",
            headers=admin_headers
        )
        assert response.status_code == 404

    def test_list_templates(self, client, admin_headers, sample_template):
        """Test listing templates"""
        response = client.get("/api/sms/templates/", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    def test_list_active_templates(self, client, admin_headers, sample_template):
        """Test listing only active templates"""
        response = client.get(
            "/api/sms/templates/?is_active=true",
            headers=admin_headers
        )
        assert response.status_code == 200
        for template in response.json():
            assert template["is_active"] == True

    def test_update_template_success(self, client, operator_headers, sample_template):
        """Test successful template update"""
        response = client.put(
            f"/api/sms/templates/{sample_template.id}",
            headers=operator_headers,
            json={
                "name": "Updated Template",
                "content": "Updated content",
                "is_active": False
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Template"
        assert data["is_active"] == False

    def test_delete_template_success(self, client, operator_headers, sample_template, db_session):
        """Test successful template deletion"""
        # Create a task for this template first
        from app.models.models import SmsTask
        task = SmsTask(
            task_id="SMS-DELTEST-001",
            template_id=str(sample_template.id),
            phone_numbers=["13800138000"],
            user_ids=[],
            variables_data={},
            status="pending"
        )
        db_session.add(task)
        db_session.commit()
        
        response = client.delete(
            f"/api/sms/templates/{sample_template.id}",
            headers=operator_headers
        )
        # API currently allows deletion even with tasks (cascade behavior)
        assert response.status_code == 200

    def test_delete_template_no_task(self, client, operator_headers, sample_template, db_session):
        """Test deleting template with no associated tasks"""
        response = client.delete(
            f"/api/sms/templates/{sample_template.id}",
            headers=operator_headers
        )
        assert response.status_code == 200


class TestSMSTasks:
    """Test SMS task endpoints"""

    def test_create_task_success(self, client, operator_headers, sample_template, sample_channel):
        """Test successful task creation"""
        response = client.post(
            "/api/sms/tasks/",
            headers=operator_headers,
            json={
                "template_id": sample_template.id,
                "channel_id": sample_channel.id,
                "recipient_count": 100,
                "phones": ["13800138000", "13800138001"]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["recipient_count"] == 2
        assert data["status"] == "pending"

    def test_create_task_invalid_template(self, client, operator_headers, sample_channel):
        """Test creating task with invalid template"""
        response = client.post(
            "/api/sms/tasks/",
            headers=operator_headers,
            json={
                "template_id": 99999,
                "channel_id": sample_channel.id,
                "recipient_count": 100,
                "phones": ["13800138000"]
            }
        )
        assert response.status_code == 400
        assert "template" in response.json()["detail"].lower()

    def test_create_task_inactive_template(self, client, operator_headers, sample_template, sample_channel, db_session):
        """Test creating task with inactive template"""
        sample_template.status = "inactive"
        db_session.commit()
        
        response = client.post(
            "/api/sms/tasks/",
            headers=operator_headers,
            json={
                "template_id": sample_template.id,
                "channel_id": sample_channel.id,
                "recipient_count": 100,
                "phones": ["13800138000"]
            }
        )
        assert response.status_code == 400
        assert "not active" in response.json()["detail"].lower()

    def test_create_task_invalid_channel(self, client, operator_headers, sample_template):
        """Test creating task with invalid channel"""
        response = client.post(
            "/api/sms/tasks/",
            headers=operator_headers,
            json={
                "template_id": sample_template.id,
                "channel_id": 99999,
                "recipient_count": 100,
                "phones": ["13800138000"]
            }
        )
        assert response.status_code == 400
        assert "channel" in response.json()["detail"].lower()

    def test_create_task_inactive_channel(self, client, operator_headers, sample_template, sample_channel, db_session):
        """Test creating task with inactive channel"""
        sample_channel.is_active = False
        sample_channel.status = ChannelStatus.INACTIVE
        db_session.commit()
        
        response = client.post(
            "/api/sms/tasks/",
            headers=operator_headers,
            json={
                "template_id": sample_template.id,
                "channel_id": sample_channel.id,
                "recipient_count": 100,
                "phones": ["13800138000"]
            }
        )
        assert response.status_code == 400
        assert "not available" in response.json()["detail"].lower()

    def test_get_task_success(self, client, admin_headers, sample_task):
        """Test getting task by ID"""
        response = client.get(
            f"/api/sms/tasks/{sample_task.id}",
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_task.id

    def test_get_nonexistent_task(self, client, admin_headers):
        """Test getting nonexistent task"""
        response = client.get(
            "/api/sms/tasks/99999",
            headers=admin_headers
        )
        assert response.status_code == 404

    def test_list_tasks(self, client, admin_headers, sample_task):
        """Test listing tasks"""
        response = client.get("/api/sms/tasks/", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    def test_list_tasks_with_status_filter(self, client, admin_headers, sample_task):
        """Test listing tasks with status filter"""
        response = client.get(
            "/api/sms/tasks/?status=pending",
            headers=admin_headers
        )
        assert response.status_code == 200
        for task in response.json():
            assert task["status"] == "pending"

    def test_send_task_success(self, client, operator_headers, sample_task, db_session):
        """Test sending SMS task"""
        # Set task to pending
        sample_task.status = SMSTaskStatus.PENDING
        db_session.commit()
        
        response = client.post(
            f"/api/sms/tasks/{sample_task.id}/send",
            headers=operator_headers
        )
        assert response.status_code == 200
        assert "sent successfully" in response.json()["message"].lower()

    def test_send_already_sent_task(self, client, operator_headers, sample_task, db_session):
        """Test sending already sent task"""
        sample_task.status = SMSTaskStatus.SUCCESS
        db_session.commit()
        
        response = client.post(
            f"/api/sms/tasks/{sample_task.id}/send",
            headers=operator_headers
        )
        assert response.status_code == 400

    def test_delete_task_success(self, client, operator_headers, sample_task, db_session):
        """Test successful task deletion"""
        sample_task.status = SMSTaskStatus.PENDING
        db_session.commit()
        
        response = client.delete(
            f"/api/sms/tasks/{sample_task.id}",
            headers=operator_headers
        )
        assert response.status_code == 200

    def test_delete_sent_task_forbidden(self, client, operator_headers, sample_task, db_session):
        """Test cannot delete sent task"""
        sample_task.status = SMSTaskStatus.SUCCESS
        db_session.commit()
        
        response = client.delete(
            f"/api/sms/tasks/{sample_task.id}",
            headers=operator_headers
        )
        assert response.status_code == 400
        assert "sent" in response.json()["detail"].lower() or "success" in response.json()["detail"].lower()
