import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

def test_ingest_message_success():
    url = f"{BASE_URL}/ingest"
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "message": "Hello, this is a test message.",
        "channel": "web",
        "sender": "test_sender",
        "timestamp": "2025-10-04T12:00:00Z"
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=TIMEOUT)
        assert response.status_code == 202, f"Expected status 202, got {response.status_code}"
    except requests.RequestException as e:
        assert False, f"Request failed: {e}"

test_ingest_message_success()