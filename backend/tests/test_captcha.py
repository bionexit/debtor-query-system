"""
Test cases for Captcha API (captcha.py)
Covering: generate, verify
"""
import pytest


class TestCaptchaGenerate:
    """Test GET /api/captcha/generate"""

    def test_generate_captcha_success(self, client):
        """Test successful captcha generation"""
        response = client.get("/api/captcha/generate")
        assert response.status_code == 200
        data = response.json()
        assert "captcha_key" in data
        assert "captcha_image" in data or "image_data" in data

    def test_generate_captcha_format(self, client):
        """Test captcha response format"""
        response = client.get("/api/captcha/generate")
        assert response.status_code == 200
        data = response.json()
        # Check that we have a valid key and image data
        assert len(data.get("captcha_key", "")) > 0


class TestCaptchaVerify:
    """Test POST /api/captcha/verify"""

    def test_verify_valid_captcha(self, client):
        """Test verifying a valid captcha"""
        # First generate a captcha
        gen_response = client.get("/api/captcha/generate")
        assert gen_response.status_code == 200
        captcha_data = gen_response.json()
        captcha_key = captcha_data.get("captcha_key")
        captcha_code = captcha_data.get("captcha_code", "12345")  # Default mock code

        # Verify the captcha
        response = client.post(
            "/api/captcha/verify",
            json={
                "captcha_key": captcha_key,
                "captcha_code": captcha_code
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("valid") is True or data.get("success") is True

    def test_verify_invalid_captcha(self, client):
        """Test verifying with invalid captcha code"""
        # Generate captcha first
        gen_response = client.get("/api/captcha/generate")
        captcha_key = gen_response.json().get("captcha_key")

        # Verify with wrong code
        response = client.post(
            "/api/captcha/verify",
            json={
                "captcha_key": captcha_key,
                "captcha_code": "00000"
            }
        )
        assert response.status_code in [200, 400]
        data = response.json()
        # Should indicate invalid
        if response.status_code == 200:
            assert data.get("valid") is False or data.get("success") is False

    def test_verify_nonexistent_captcha(self, client):
        """Test verifying non-existent captcha key"""
        response = client.post(
            "/api/captcha/verify",
            json={
                "captcha_key": "nonexistent_key_12345",
                "captcha_code": "12345"
            }
        )
        assert response.status_code == 404

    def test_verify_missing_fields(self, client):
        """Test verify with missing fields"""
        response = client.post(
            "/api/captcha/verify",
            json={"captcha_key": "some_key"}
        )
        assert response.status_code == 422

    def test_verify_empty_body(self, client):
        """Test verify with empty body"""
        response = client.post("/api/captcha/verify", json={})
        assert response.status_code == 422
