import requests
from requests.auth import HTTPBasicAuth

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

def test_get_system_health_status():
    url = f"{BASE_URL}/health"
    try:
        response = requests.get(url, timeout=TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as e:
        assert False, f"Request failed: {e}"
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"

    data = response.json()
    assert isinstance(data, dict), "Response is not a JSON object"
    for field in ["status", "timestamp", "version", "environment"]:
        assert field in data, f"Missing field '{field}' in response"
        assert isinstance(data[field], str), f"Field '{field}' is not a string"
    
test_get_system_health_status()