import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

def test_get_database_health_status():
    url = f"{BASE_URL}/health/database"
    try:
        response = requests.get(url, timeout=TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as e:
        assert False, f"Request to {url} failed: {e}"

    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"

    json_data = response.json()
    assert isinstance(json_data, dict), "Response JSON is not a dictionary"
    assert "status" in json_data, "'status' key missing in response"
    assert "database" in json_data, "'database' key missing in response"
    assert "connected" in json_data, "'connected' key missing in response"

    assert isinstance(json_data["status"], str), "'status' is not a string"
    assert isinstance(json_data["database"], str), "'database' is not a string"
    assert isinstance(json_data["connected"], bool), "'connected' is not a boolean"

# Call the test function
test_get_database_health_status()