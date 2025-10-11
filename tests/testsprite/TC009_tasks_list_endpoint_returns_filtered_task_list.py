import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 30
TASKS_ENDPOINT = f"{BASE_URL}/tasks"


def test_tasks_list_endpoint_returns_filtered_task_list():
    """
    Test the /tasks GET endpoint with various query parameters (status, limit, offset)
    to verify it returns a filtered list of tasks with correct pagination and total count.
    """
    try:
        # Define a set of test queries to validate filtering, pagination, and total count
        test_queries = [
            {"params": {}, "description": "No filters - default pagination"},
            {"params": {"status": "pending"},
                "description": "Filter by status=pending"},
            {"params": {"status": "in_progress", "limit": 5},
                "description": "Filter by status=in_progress and limit=5"},
            {"params": {"limit": 10, "offset": 2},
                "description": "Pagination only with limit=10 and offset=2"},
            {"params": {"status": "completed", "limit": 3, "offset": 1},
                "description": "Filter by completed and pagination"},
            {"params": {"status": "cancelled", "limit": 1},
                "description": "Filter by cancelled with limit=1"},
        ]

        for test_case in test_queries:
            params = test_case["params"]
            description = test_case["description"]
            response = requests.get(
                TASKS_ENDPOINT, params=params, timeout=TIMEOUT)
            assert response.status_code == 200, f"Expected 200 OK for {description}, got {response.status_code}"
            json_data = response.json()

            # Validate presence and types of keys
            assert isinstance(
                json_data, dict), f"Response for {description} is not an object"
            assert "tasks" in json_data, f"'tasks' key missing in response for {description}"
            assert "total" in json_data, f"'total' key missing in response for {description}"
            assert "limit" in json_data, f"'limit' key missing in response for {description}"
            assert "offset" in json_data, f"'offset' key missing in response for {description}"

            tasks = json_data["tasks"]
            total = json_data["total"]
            limit = json_data["limit"]
            offset = json_data["offset"]

            assert isinstance(
                tasks, list), f"'tasks' is not a list for {description}"
            assert isinstance(
                total, int), f"'total' is not int for {description}"
            assert isinstance(
                limit, int), f"'limit' is not int for {description}"
            assert isinstance(
                offset, int), f"'offset' is not int for {description}"

            # Validate limit and offset match query if provided
            if "limit" in params:
                assert limit == params[
                    "limit"], f"Returned limit does not match requested for {description}"
                assert limit <= 100, f"Limit exceeds maximum 100 for {description}"
            else:
                assert limit <= 100, f"Default limit exceeds maximum 100 for {description}"

            if "offset" in params:
                assert offset == params[
                    "offset"], f"Returned offset does not match requested for {description}"
            else:
                assert offset == 0, f"Default offset should be 0 for {description}"

            # Validate tasks length does not exceed limit
            assert len(
                tasks) <= limit, f"Number of tasks exceeds limit for {description}"

            # If status filter applied, all tasks should match status
            if "status" in params:
                valid_statuses = {"pending", "in_progress",
                                  "completed", "cancelled"}
                filter_status = params["status"]
                assert filter_status in valid_statuses, f"Invalid status filter used: {filter_status}"
                for task in tasks:
                    assert isinstance(
                        task, dict), f"Task item not a dict in {description}"
                    task_status = task.get("status")
                    assert task_status == filter_status, f"Task status '{task_status}' doesn't match filter '{filter_status}' in {description}"

            # total represents the total count of tasks for the applied filter (>= length of tasks returned)
            assert total >= len(
                tasks), f"Total {total} less than tasks returned {len(tasks)} for {description}"

    except requests.RequestException as e:
        assert False, f"Request failed: {e}"
    except AssertionError as e:
        raise
    except Exception as e:
        assert False, f"Unexpected error: {e}"


test_tasks_list_endpoint_returns_filtered_task_list()
