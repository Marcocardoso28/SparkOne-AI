import requests
from requests.auth import HTTPBasicAuth

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

# Assuming credentials for HTTP Basic Auth are required as per PRD
USERNAME = "testuser"
PASSWORD = "testpass"


def test_create_new_task_with_valid_data():
    auth = HTTPBasicAuth(USERNAME, PASSWORD)
    headers = {"Content-Type": "application/json"}

    # Prepare valid task payload with required and optional fields
    payload = {
        "title": "Complete integration test",
        "description": "Verify task creation with all required and optional fields",
        "due_at": "2025-12-31T23:59:59Z",
        "channel": "web",
        "sender": "tester",
        "priority": "high"
    }

    task_id = None

    # Create new task via POST /tasks
    response = requests.post(
        f"{BASE_URL}/tasks",
        json=payload,
        auth=auth,
        headers=headers,
        timeout=TIMEOUT,
    )
    assert response.status_code == 201, f"Expected 201 but got {response.status_code}"
    task = response.json()

    # Validate response content matches input fields and has expected properties
    assert "id" in task and isinstance(task["id"], int), "Task ID missing or invalid"
    assert task["title"] == payload["title"], "Title does not match"
    assert task.get("description") == payload["description"], "Description does not match"

    due_date = task.get("due_date")
    if due_date is not None:
        assert isinstance(due_date, str), "Due date format invalid"

    assert task["channel"] == payload["channel"], "Channel does not match"
    assert task["sender"] == payload["sender"], "Sender does not match"
    assert task.get("priority") == payload["priority"], "Priority does not match"
    assert "status" in task and isinstance(task["status"], str), "Status missing or invalid"
    assert "created_at" in task and isinstance(task["created_at"], str), "created_at missing or invalid"
    assert "updated_at" in task and isinstance(task["updated_at"], str), "updated_at missing or invalid"

    task_id = task["id"]

    # Additional checks: List tasks to confirm new task is present
    list_response = requests.get(
        f"{BASE_URL}/tasks",
        params={"channel": payload["channel"], "limit": 10, "offset": 0},
        auth=auth,
        timeout=TIMEOUT,
    )
    assert list_response.status_code == 200, f"Expected 200 but got {list_response.status_code} in list tasks"
    list_data = list_response.json()
    assert "tasks" in list_data and isinstance(list_data["tasks"], list), "tasks list missing"
    assert any(t["id"] == task_id for t in list_data["tasks"]), "Created task not found in task list"


test_create_new_task_with_valid_data()
