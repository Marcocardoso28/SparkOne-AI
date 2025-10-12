import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 30


def test_health_database_endpoint_returns_database_health_status():
    url = f"{BASE_URL}/health/database"
    try:
        response = requests.get(url, timeout=TIMEOUT)
    except requests.RequestException as e:
        assert False, f"Request to {url} failed: {e}"

    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"


test_health_database_endpoint_returns_database_health_status()
