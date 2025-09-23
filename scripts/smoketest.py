"""Perform quick smoke tests against a running SparkOne instance."""

from __future__ import annotations

import argparse
import sys
from typing import Any

import httpx


def test_endpoint(client: httpx.Client, path: str, expected_status: int = 200) -> tuple[bool, str]:
    url = client.base_url.join(path)
    try:
        response = client.get(url)
    except httpx.HTTPError as exc:  # pragma: no cover - manual script
        return False, f"{path}: request failed ({exc})"
    if response.status_code != expected_status:
        return False, f"{path}: unexpected status {response.status_code}"
    return True, f"{path}: ok"


def main() -> None:
    parser = argparse.ArgumentParser(description="SparkOne smoke tests")
    parser.add_argument("--base-url", required=True, help="Base URL da instância (ex.: https://sparkone.dev)")
    parser.add_argument("--web-password", help="Senha da Web UI (para testar /web)")
    args = parser.parse_args()

    results: list[tuple[bool, str]] = []
    with httpx.Client(base_url=args.base_url, timeout=5) as client:
        for path in ["/health/", "/health/database", "/health/openai", "/health/notion", "/metrics"]:
            results.append(test_endpoint(client, path, expected_status=200 if "metrics" not in path else 200))

        # Optional web auth smoke test
        if args.web_password:
            auth = ("smoketest", args.web_password)
            results.append(test_endpoint(client, "/web", expected_status=401))
            results.append(test_endpoint(httpx.Client(base_url=args.base_url, auth=auth, timeout=5), "/web", expected_status=200))

    failures = [msg for ok, msg in results if not ok]
    for ok, msg in results:
        prefix = "[OK]" if ok else "[FAIL]"
        print(f"{prefix} {msg}")

    if failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
