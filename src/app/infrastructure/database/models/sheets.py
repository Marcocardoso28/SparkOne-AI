"""Persistence models for Google Sheets sync state."""

from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class SheetsSyncStateORM(TimestampMixin, Base):
    __tablename__ = "sheets_sync_state"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    spreadsheet_id: Mapped[str] = mapped_column(nullable=False)
    range_name: Mapped[str] = mapped_column(nullable=False)
    last_row_index: Mapped[int] = mapped_column(nullable=False, default=0)


__all__ = ["SheetsSyncStateORM"]
