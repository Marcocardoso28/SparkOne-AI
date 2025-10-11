import requests
from requests.auth import HTTPBasicAuth

BASE_URL = "http://localhost:8000"
USERNAME = "testuser"
PASSWORD = "testpass"


def test_update_task_status_success():
    auth = HTTPBasicAuth(USERNAME, PASSWORD)
    headers = {"Content-Type": "application/json"}
    created_task_id = None

    try:
        # Create a new task to update
        create_payload = {
            "title": "Test Task for Status Update",
            "channel": "test_channel",
            "sender": "test_sender",
            "description": "Task description for update test",
            "priority": "medium"
        }
        create_resp = requests.post(
            f"{BASE_URL}/tasks",
            json=create_payload,
            auth=auth,
            headers=headers,
            timeout=30
        )
        assert create_resp.status_code == 201, f"Failed to create task: {create_resp.text}"
        task = create_resp.json()
        created_task_id = task.get("id")
        assert isinstance(created_task_id, int), "Created task ID is not an integer"

        # Update the status of the created task
        new_status = "completed"
        update_payload = {"status": new_status}
        update_resp = requests.patch(
            f"{BASE_URL}/tasks/{created_task_id}/status",
            json=update_payload,
            auth=auth,
            headers=headers,
            timeout=30
        )
        assert update_resp.status_code == 200, f"Failed to update task status: {update_resp.text}"

        # Verify status updated by retrieving task list filtered by status and id
        list_resp = requests.get(
            f"{BASE_URL}/tasks",
            auth=auth,
            headers=headers,
            params={"status": new_status, "limit": 10},
            timeout=30
        )
        assert list_resp.status_code == 200, f"Failed to list tasks: {list_resp.text}"
        tasks_data = list_resp.json()
        assert "tasks" in tasks_data, "Response JSON missing 'tasks' key"
        tasks = tasks_data["tasks"]
        matching_task = next((t for t in tasks if t.get("id") == created_task_id), None)
        assert matching_task is not None, "Updated task not found in filtered task list"
        assert matching_task.get("status") == new_status, "Task status did not update correctly"

    finally:
        # Clean up - delete the created task
        if created_task_id is not None:
            requests.delete(
                f"{BASE_URL}/tasks/{created_task_id}",
                auth=auth,
                headers=headers,
                timeout=30
            )


test_update_task_status_success()