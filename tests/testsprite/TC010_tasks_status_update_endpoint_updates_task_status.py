import requests
import json

BASE_URL = "http://localhost:8000"
TIMEOUT = 30
HEADERS = {"Content-Type": "application/json"}
CREATE_TASK_PAYLOAD = {
    "title": "Test Task for status update",
    "description": "Task created for testing status update endpoint",
    "status": "pending",
    "priority": "medium"
}
CREATE_TASK_ENDPOINT = f"{BASE_URL}/tasks"
TASK_STATUS_ENDPOINT_TEMPLATE = f"{BASE_URL}/tasks/{{task_id}}/status"


def create_task():
    # Create a task to get a valid task_id
    resp = requests.post(CREATE_TASK_ENDPOINT, headers={
                         "Content-Type": "application/json"}, json=CREATE_TASK_PAYLOAD, timeout=TIMEOUT)
    resp.raise_for_status()
    task = resp.json()
    # We expect the created task to have an 'id' field
    return task["id"]


def delete_task(task_id):
    # Delete the created task to clean up after test
    resp = requests.delete(f"{BASE_URL}/tasks/{task_id}", timeout=TIMEOUT)
    resp.raise_for_status()


def test_tasks_status_update_endpoint_updates_task_status():
    task_id = None
    try:
        # Create task to update
        task_id = create_task()

        # Test updating status to a valid status "completed"
        patch_payload = {"status": "completed"}
        resp = requests.patch(
            TASK_STATUS_ENDPOINT_TEMPLATE.format(task_id=task_id),
            headers=HEADERS,
            json=patch_payload,
            timeout=TIMEOUT
        )
        assert resp.status_code == 200, f"Expected 200 on successful status update, got {resp.status_code}"
        # Optionally verify the returned content reflects the updated status
        data = resp.json()
        assert "status" in data, "Response JSON must include 'status'"
        assert data["status"] == "completed", "Task status was not updated correctly"

        # Test updating a non-existent task returns 404
        invalid_task_id = 9999999999
        resp_not_found = requests.patch(
            TASK_STATUS_ENDPOINT_TEMPLATE.format(task_id=invalid_task_id),
            headers=HEADERS,
            json=patch_payload,
            timeout=TIMEOUT
        )
        assert resp_not_found.status_code == 404, f"Expected 404 for non-existent task, got {resp_not_found.status_code}"

    finally:
        if task_id is not None:
            delete_task(task_id)


test_tasks_status_update_endpoint_updates_task_status()
