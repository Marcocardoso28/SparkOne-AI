import requests
from requests.auth import HTTPBasicAuth

BASE_URL = "http://localhost:8000"
TIMEOUT = 30
AUTH_USERNAME = "admin"
AUTH_PASSWORD = "password"

def test_list_tasks_with_filters_and_pagination():
    auth = HTTPBasicAuth(AUTH_USERNAME, AUTH_PASSWORD)

    # First create multiple tasks with different status and channel for filtering test
    created_task_ids = []
    try:
        tasks_to_create = [
            {"title": "Task 1", "channel": "web", "sender": "user1", "priority": "high", "description": "First task", "due_at": "2025-12-31T23:59:59Z"},
            {"title": "Task 2", "channel": "whatsapp", "sender": "user2", "priority": "low", "description": "Second task", "due_at": "2025-12-20T12:00:00Z"},
            {"title": "Task 3", "channel": "web", "sender": "user3", "priority": "medium", "description": "Third task", "due_at": "2025-11-15T15:30:00Z"},
            {"title": "Task 4", "channel": "whatsapp", "sender": "user1", "priority": "high", "description": "Fourth task", "due_at": "2025-10-10T10:10:10Z"},
            {"title": "Task 5", "channel": "web", "sender": "user2", "priority": "low", "description": "Fifth task", "due_at": "2025-09-09T09:09:09Z"},
        ]
        for task in tasks_to_create:
            resp = requests.post(
                f"{BASE_URL}/tasks",
                auth=auth,
                json=task,
                timeout=TIMEOUT
            )
            assert resp.status_code == 201, f"Failed to create task: {resp.text}"
            data = resp.json()
            assert "id" in data, "Created task missing 'id'"
            created_task_ids.append(data["id"])

        # Update some tasks' statuses for testing status filter
        # Let's update Task 1 and Task 4 to status 'completed'
        update_status_map = {
            created_task_ids[0]: "completed",
            created_task_ids[3]: "completed"
        }
        for task_id, status in update_status_map.items():
            resp = requests.patch(
                f"{BASE_URL}/tasks/{task_id}/status",
                auth=auth,
                json={"status": status},
                timeout=TIMEOUT
            )
            assert resp.status_code == 200, f"Failed to update task status for {task_id}: {resp.text}"

        # Now test GET /tasks with filters and pagination
        # Filters: status=completed, channel=web, limit=1, offset=0
        params = {
            "status": "completed",
            "channel": "web",
            "limit": 1,
            "offset": 0
        }
        resp = requests.get(
            f"{BASE_URL}/tasks",
            auth=auth,
            params=params,
            timeout=TIMEOUT
        )
        assert resp.status_code == 200, f"Failed to fetch tasks with filters: {resp.text}"
        resp_json = resp.json()

        # Validate response structure
        assert "tasks" in resp_json, "Response missing 'tasks'"
        assert "total" in resp_json, "Response missing 'total'"
        assert "limit" in resp_json, "Response missing 'limit'"
        assert "offset" in resp_json, "Response missing 'offset'"

        # Validate pagination fields match request
        assert resp_json["limit"] == params["limit"], f"Limit mismatch, expected {params['limit']}, got {resp_json['limit']}"
        assert resp_json["offset"] == params["offset"], f"Offset mismatch, expected {params['offset']}, got {resp_json['offset']}"

        # Validate tasks returned filtered by status and channel
        tasks = resp_json["tasks"]
        assert isinstance(tasks, list), "'tasks' is not a list"
        assert len(tasks) <= params["limit"], "Returned tasks exceed limit"

        for task in tasks:
            # Check task properties exist
            assert "id" in task, "Task missing 'id'"
            assert "status" in task, "Task missing 'status'"
            assert "channel" in task, "Task missing 'channel'"
            # Validate filtering
            assert task["status"] == params["status"], f"Task status '{task['status']}' does not match filter '{params['status']}'"
            assert task["channel"] == params["channel"], f"Task channel '{task['channel']}' does not match filter '{params['channel']}'"

        # Also test offset works by requesting offset=1 to get the next page
        params2 = params.copy()
        params2["offset"] = 1
        resp2 = requests.get(
            f"{BASE_URL}/tasks",
            auth=auth,
            params=params2,
            timeout=TIMEOUT
        )
        assert resp2.status_code == 200, f"Failed to fetch tasks with offset: {resp2.text}"
        resp2_json = resp2.json()
        assert resp2_json["offset"] == 1, "Offset in response does not match requested offset"

        # The total should be equal or greater than the task count matching the filter (which is >= 1)
        total_expected = resp_json["total"]
        total_second_call = resp2_json["total"]
        assert total_second_call == total_expected, "Total count mismatch between requests"

    finally:
        # Cleanup: delete created tasks to maintain test isolation
        for task_id in created_task_ids:
            try:
                resp_del = requests.delete(f"{BASE_URL}/tasks/{task_id}", auth=auth, timeout=TIMEOUT)
                # It might be 204 No Content or 200 OK, allow both
                assert resp_del.status_code in (200, 204), f"Failed to delete task {task_id}, status {resp_del.status_code}"
            except Exception:
                pass

test_list_tasks_with_filters_and_pagination()