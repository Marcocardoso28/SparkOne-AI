import requests

BASE_URL = "http://localhost:8000"
LOGIN_ENDPOINT = f"{BASE_URL}/auth/login"
TIMEOUT = 30

def test_user_login_with_invalid_credentials():
    url = LOGIN_ENDPOINT
    headers = {
        "Content-Type": "application/json"
    }
    invalid_payload = {
        "username": "invalid_user",
        "password": "wrong_password"
    }
    try:
        response = requests.post(url, json=invalid_payload, headers=headers, timeout=TIMEOUT)
    except requests.exceptions.RequestException as e:
        assert False, f"Request failed: {e}"

    assert response.status_code == 401, (
        f"Expected status code 401 for invalid credentials, got {response.status_code}. "
        f"Response body: {response.text}"
    )

test_user_login_with_invalid_credentials()
