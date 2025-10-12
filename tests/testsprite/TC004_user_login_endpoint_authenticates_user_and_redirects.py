import requests

BASE_URL = "http://localhost:8000"
LOGIN_ENDPOINT = f"{BASE_URL}/web/login"
TIMEOUT = 30


def test_user_login_endpoint_authenticates_and_redirects():
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    # Valid credentials example (change to valid values if known)
    valid_payload = {
        "username": "validuser@example.com",
        "password": "ValidPassword123!"
    }
    # Invalid credentials example
    invalid_payload = {
        "username": "invaliduser@example.com",
        "password": "WrongPassword!"
    }

    # Test valid login
    try:
        response = requests.post(LOGIN_ENDPOINT, data=valid_payload,
                                 headers=headers, allow_redirects=False, timeout=TIMEOUT)
        # Should redirect on success: status code 302
        assert response.status_code == 302, f"Expected status code 302 on valid login, got {response.status_code}"
        # Location header should be present for redirect URL
        assert "Location" in response.headers, "Missing 'Location' header on successful login redirect"
        # Session creation can be inferred from Set-Cookie header presence
        assert "Set-Cookie" in response.headers and response.headers[
            "Set-Cookie"], "Expected 'Set-Cookie' header for session creation on valid login"
    except requests.RequestException as e:
        assert False, f"Request error during valid login test: {e}"

    # Test invalid login
    try:
        response = requests.post(LOGIN_ENDPOINT, data=invalid_payload,
                                 headers=headers, allow_redirects=False, timeout=TIMEOUT)
        # Should not redirect - expecting non-302 status, likely 401 or 400
        assert response.status_code != 302, f"Did not expect redirect on invalid login but got status {response.status_code}"
        # Typically, after failed login, status is 401 Unauthorized or 400 Bad Request; checking in these expected ranges
        assert response.status_code in [
            400, 401, 403], f"Unexpected status code for invalid login: {response.status_code}"
    except requests.RequestException as e:
        assert False, f"Request error during invalid login test: {e}"


test_user_login_endpoint_authenticates_and_redirects()
