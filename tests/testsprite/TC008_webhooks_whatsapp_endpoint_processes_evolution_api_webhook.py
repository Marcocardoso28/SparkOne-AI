import requests


def test_webhooks_whatsapp_post_process_evolution_api_webhook():
    base_url = "http://localhost:8000"
    url = f"{base_url}/webhooks/whatsapp"
    headers = {
        "Content-Type": "application/json"
    }
    # Example payload similar to the schema defined in the PRD
    payload = {
        "data": {
            "key": {
                "remoteJid": "5511999999999@s.whatsapp.net",
                "fromMe": False,
                "id": "ABGGFlA5FpA5Nzc1",
                "participant": "5511988888888@s.whatsapp.net"
            },
            "message": {
                "conversation": "Test message from Evolution API webhook"
            },
            "messageTimestamp": 1715145600
        }
    }

    try:
        response = requests.post(url, headers=headers,
                                 json=payload, timeout=30)
        assert response.status_code == 202, f"Expected status 202 but got {response.status_code}"
    except requests.RequestException as e:
        assert False, f"Request failed: {e}"


test_webhooks_whatsapp_post_process_evolution_api_webhook()
