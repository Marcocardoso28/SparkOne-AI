import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 30


def test_health_redis_endpoint_returns_redis_health_status():
    url = f"{BASE_URL}/health/redis"
    headers = {
        "Accept": "application/json"
    }

    try:
        response = requests.get(url, headers=headers, timeout=TIMEOUT)
    except requests.RequestException as e:
        assert False, f"Request to /health/redis failed: {e}"

    assert response.status_code == 200, f"Expected status code 200 but got {response.status_code}"


test_health_redis_endpoint_returns_redis_health_status()
