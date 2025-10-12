import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

def test_get_redis_health_status():
    url = f"{BASE_URL}/health/redis"
    try:
        response = requests.get(url, timeout=TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as e:
        assert False, f"Request to {url} failed: {e}"

    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"

    json_data = response.json()
    # Validate required fields presence and types
    assert "status" in json_data and isinstance(json_data["status"], str), "Missing or invalid 'status'"
    assert "redis" in json_data and isinstance(json_data["redis"], str), "Missing or invalid 'redis'"
    assert "connected" in json_data and isinstance(json_data["connected"], bool), "Missing or invalid 'connected'"

test_get_redis_health_status()