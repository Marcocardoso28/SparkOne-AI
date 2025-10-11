import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 30


def test_health_general_endpoint_returns_system_health_status():
    url = f"{BASE_URL}/health"
    try:
        response = requests.get(url, timeout=TIMEOUT)
        if response.status_code == 200:
            # Expect system healthy message or indication in response body (if any)
            assert response.ok
        elif response.status_code == 503:
            # System has issues, no body requirements asserted due to PRD info
            assert response.status_code == 503
        else:
            # Unexpected status code
            assert False, f"Unexpected status code: {response.status_code}"
    except requests.RequestException as e:
        assert False, f"Request failed: {e}"


test_health_general_endpoint_returns_system_health_status()
