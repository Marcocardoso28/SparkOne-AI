"""Management CLI for administrative tasks.

Usage (inside container):
  python -m app.manage create-admin --email admin@example.com --password 'Secret123' [--superuser]
"""

from __future__ import annotations

import argparse
import asyncio
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.database import get_engine, get_session_factory
from app.models.db.user import User
from app.services.passwords import hash_password


async def _create_admin(email: str, password: str, superuser: bool) -> None:
    settings = get_settings()
    session_factory = get_session_factory()
    # Ensure 'users' table exists (create if missing)
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: User.__table__.create(bind=sync_conn, checkfirst=True))
    async with session_factory() as session:  # type: AsyncSession
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user is None:
            user = User(
                email=email,
                password_hash=hash_password(password),
                is_active=True,
                is_verified=True,
                last_login=datetime.utcnow(),
                is_admin=superuser,
            )
            session.add(user)
            await session.commit()
            print(f"Admin user created: {email} (is_admin={superuser})")
        else:
            user.password_hash = hash_password(password)
            user.is_active = True
            user.is_verified = True
            if superuser:
                user.is_admin = True
            await session.commit()
            print(f"Admin user updated: {email} (is_admin={user.is_admin})")


def main() -> None:
    parser = argparse.ArgumentParser(description="SparkOne management CLI")
    sub = parser.add_subparsers(dest="cmd")

    a = sub.add_parser("create-admin", help="Create or update an admin user")
    a.add_argument("--email", required=True)
    a.add_argument("--password", required=True)
    a.add_argument("--superuser", action="store_true", help="Mark user as admin")

    args = parser.parse_args()
    if args.cmd == "create-admin":
        asyncio.run(_create_admin(args.email, args.password, bool(args.superuser)))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
