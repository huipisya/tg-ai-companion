from pathlib import Path

import asyncpg
from config import DATABASE_URL

_MIGRATIONS_DIR = Path(__file__).parent / "migrations"

_pool: asyncpg.Pool | None = None


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)
    return _pool


async def close_pool() -> None:
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


async def run_migrations() -> None:
    pool = await get_pool()
    with open(_MIGRATIONS_DIR / "001_init.sql") as f:
        sql = f.read()
    async with pool.acquire() as conn:
        await conn.execute(sql)
