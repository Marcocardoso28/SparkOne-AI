"""Google Sheets integration helpers."""

from __future__ import annotations

import asyncio
from typing import Any, Sequence

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build


SCOPES: Sequence[str] = ("https://www.googleapis.com/auth/spreadsheets",)


class GoogleSheetsClient:
    """Wrapper around Google Sheets API v4 using service account credentials."""

    def __init__(self, credentials_path: str) -> None:
        self._credentials = Credentials.from_service_account_file(credentials_path, scopes=SCOPES)
        self._service = build("sheets", "v4", credentials=self._credentials, cache_discovery=False)

    async def list_rows(self, spreadsheet_id: str, range_: str) -> list[list[Any]]:
        def _list_rows() -> list[list[Any]]:
            result = (
                self._service.spreadsheets()
                .values()
                .get(spreadsheetId=spreadsheet_id, range=range_)
                .execute()
            )
            return result.get("values", [])

        return await asyncio.to_thread(_list_rows)

    async def append_row(self, spreadsheet_id: str, range_: str, values: list[Any]) -> None:
        def _append_row() -> None:
            body = {"values": [values]}
            self._service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range=range_,
                valueInputOption="USER_ENTERED",
                insertDataOption="INSERT_ROWS",
                body=body,
            ).execute()

        await asyncio.to_thread(_append_row)


__all__ = ["GoogleSheetsClient", "SCOPES"]
