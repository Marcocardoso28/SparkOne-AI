import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 30


def test_channels_endpoint_normalizes_and_accepts_channel_specific_payloads():
    headers = {"Content-Type": "application/json"}

    supported_channels_payloads = {
        "whatsapp": {
            "phone_number": "+5511999998888",
            "message": "Olá, esta é uma mensagem de teste via WhatsApp!",
            "timestamp": "2025-10-04T15:00:00Z"
        },
        "web": {
            "user_id": "user123",
            "message": "Mensagem de teste via Web Channel",
            "sent_at": "2025-10-04T15:05:00Z"
        },
        "sheets": {
            "spreadsheet_id": "sheet123",
            "row_data": ["valor1", "valor2", "valor3"],
            "updated_at": "2025-10-04T15:10:00Z"
        }
    }

    # Test valid payloads for registered channels: Should get 202
    for channel, payload in supported_channels_payloads.items():
        url = f"{BASE_URL}/channels/{channel}"
        try:
            response = requests.post(
                url, json=payload, headers=headers, timeout=TIMEOUT)
            assert response.status_code == 202, f"{channel} payload should be accepted with 202, got {response.status_code}"
        except requests.RequestException as e:
            assert False, f"Request to {url} failed: {e}"

    # Test invalid channel name: should get 400
    invalid_channel = "invalid_channel"
    invalid_channel_payload = {"any": "data"}
    url_invalid = f"{BASE_URL}/channels/{invalid_channel}"
    try:
        response_invalid = requests.post(
            url_invalid, json=invalid_channel_payload, headers=headers, timeout=TIMEOUT)
        assert response_invalid.status_code == 400, f"Invalid channel should return 400, got {response_invalid.status_code}"
    except requests.RequestException as e:
        assert False, f"Request to {url_invalid} failed: {e}"

    # Test registered channels with invalid payloads: should get 400
    invalid_payloads = [
        {},  # empty payload
        {"wrong_field": "value"},  # wrong fields
        {"message": 12345},  # wrong data type
        None  # None payload should be handled
    ]

    for channel in supported_channels_payloads.keys():
        url = f"{BASE_URL}/channels/{channel}"
        for invalid_payload in invalid_payloads:
            # requests.post with json=None sends no payload, which is invalid here
            try:
                if invalid_payload is None:
                    response = requests.post(
                        url, headers=headers, timeout=TIMEOUT)
                else:
                    response = requests.post(
                        url, json=invalid_payload, headers=headers, timeout=TIMEOUT)
                assert response.status_code == 400, f"Invalid payload for {channel} should return 400, got {response.status_code}"
            except requests.RequestException as e:
                assert False, f"Request to {url} with invalid payload failed: {e}"


test_channels_endpoint_normalizes_and_accepts_channel_specific_payloads()
