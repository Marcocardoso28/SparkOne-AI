import requests
from requests.auth import HTTPBasicAuth

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

# Credentials for a test user - should be valid in the test environment
TEST_USERNAME = "testuser@example.com"
TEST_PASSWORD = "TestPassword123"


def test_user_logout_endpoint_terminates_session_and_redirects():
    session = requests.Session()

    # Step 1: Login to create a session
    login_url = f"{BASE_URL}/web/login"
    login_headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    login_data = {
        "username": TEST_USERNAME,
        "password": TEST_PASSWORD
    }

    try:
        login_response = session.post(
            login_url,
            headers=login_headers,
            data=login_data,
            timeout=TIMEOUT,
            allow_redirects=False
        )
        # Assert login success via redirect status 302
        assert login_response.status_code == 302, f"Expected 302 status code on login, got {login_response.status_code}"
        # Check that session cookie is set (session should hold cookies automatically)
        assert session.cookies, "Session cookies not set after login"

        # Step 2: Call logout endpoint to terminate session
        logout_url = f"{BASE_URL}/web/logout"
        logout_response = session.post(
            logout_url,
            timeout=TIMEOUT,
            allow_redirects=False
        )

        # Assert logout returns redirect status 302
        assert logout_response.status_code == 302, f"Expected 302 status code on logout, got {logout_response.status_code}"

        # Additionally, cookie Jar of session should now not contain auth cookies or session cookies might be cleared.
        # Since we cannot guarantee cookie clearing on client-side, testing subsequent authenticated request fails is next best.
        # Attempt a request that requires auth (like /web) - expecting 401 unauthorized or redirect to login

        web_url = f"{BASE_URL}/web"
        web_response = session.get(
            web_url, timeout=TIMEOUT, allow_redirects=False)
        # We expect unauthorized (401) or redirect (302) to login page after logout
        assert web_response.status_code in (401, 302), \
            f"Expected 401 or 302 after logout accessing protected resource, got {web_response.status_code}"

    finally:
        # Clean up: attempt logout again in case test failed before logout was called
        try:
            session.post(logout_url, timeout=TIMEOUT, allow_redirects=False)
        except Exception:
            pass


test_user_logout_endpoint_terminates_session_and_redirects()
