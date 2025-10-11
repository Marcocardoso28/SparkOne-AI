import requests
from datetime import datetime, timezone

BASE_URL = "http://localhost:8000"
INGEST_ENDPOINT = f"{BASE_URL}/ingest"
TIMEOUT = 30


def test_ingest_endpoint_accepts_and_processes_normalized_messages():
    headers = {"Content-Type": "application/json"}

    valid_payloads = [
        {
            "channel": "whatsapp",
            "sender": "user_whatsapp_123",
            "content": "Olá, esta é uma mensagem do WhatsApp.",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": {"message_id": "abc-whatsapp-1"},
        },
        {
            "channel": "web",
            "sender": "user_web_456",
            "content": "Hello from the web interface!",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": {"session_id": "session-web-789"},
        },
        {
            "channel": "sheets",
            "sender": "user_sheets_789",
            "content": "Data from sheets integration.",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": {"sheet_id": "sheet-123"},
        },
    ]

    invalid_payloads = [
        # Missing required field 'channel'
        {
            "sender": "user_invalid_1",
            "content": "Missing channel field",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        # Invalid channel value
        {
            "channel": "email",
            "sender": "user_invalid_2",
            "content": "Invalid channel value",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        # Missing required field 'timestamp'
        {
            "channel": "web",
            "sender": "user_invalid_3",
            "content": "Missing timestamp",
        },
        # content exceeds max length 10,000 chars
        {
            "channel": "web",
            "sender": "user_invalid_4",
            "content": "a" * 10001,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    ]

    # Test valid payloads - expect 202
    for payload in valid_payloads:
        try:
            response = requests.post(
                INGEST_ENDPOINT, headers=headers, json=payload, timeout=TIMEOUT
            )
        except requests.RequestException as e:
            assert False, f"Request failed for valid payload: {e}"
        assert response.status_code == 202, (
            f"Expected status 202 for valid payload on channel {payload['channel']}, "
            f"got {response.status_code}, response: {response.text}"
        )

    # Test invalid payloads - expect 400
    for payload in invalid_payloads:
        try:
            response = requests.post(
                INGEST_ENDPOINT, headers=headers, json=payload, timeout=TIMEOUT
            )
        except requests.RequestException as e:
            assert False, f"Request failed for invalid payload: {e}"
        assert response.status_code == 400, (
            f"Expected status 400 for invalid payload, got {response.status_code}, "
            f"response: {response.text}"
        )


test_ingest_endpoint_accepts_and_processes_normalized_messages()
