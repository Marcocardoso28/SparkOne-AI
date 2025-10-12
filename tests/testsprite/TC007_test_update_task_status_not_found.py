import requests
from requests.auth import HTTPBasicAuth

BASE_URL = "http://localhost:8000"
TIMEOUT = 30
USERNAME = "testuser"
PASSWORD = "testpassword"

def test_update_task_status_not_found():
    # Use a very large task_id unlikely to exist
    non_existent_task_id = 999999999
    url = f"{BASE_URL}/tasks/{non_existent_task_id}/status"
    headers = {"Content-Type": "application/json"}
    payload = {"status": "completed"}

    try:
        response = requests.patch(
            url,
            json=payload,
            headers=headers,
            auth=HTTPBasicAuth(USERNAME, PASSWORD),
            timeout=TIMEOUT
        )
    except requests.RequestException as e:
        assert False, f"Request failed: {e}"

    assert response.status_code == 404, f"Expected 404 status code for non-existent task, got {response.status_code}"

test_update_task_status_not_found()