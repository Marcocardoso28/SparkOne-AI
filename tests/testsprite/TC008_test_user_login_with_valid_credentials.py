import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

def test_user_login_with_valid_credentials():
    url = f"{BASE_URL}/auth/login"
    payload = {
        "username": "valid_user",
        "password": "valid_password"
    }
    headers = {
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=TIMEOUT)
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        data = response.json()
        assert "access_token" in data and isinstance(data["access_token"], str) and data["access_token"], "access_token missing or invalid"
        assert data.get("token_type") == "bearer" or isinstance(data.get("token_type"), str), "token_type missing or invalid"
    except requests.RequestException as e:
        assert False, f"Request failed: {e}"

test_user_login_with_valid_credentials()