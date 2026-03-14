import secrets
from datetime import timedelta

import asyncpg
from database.db import get_pool

PREMIUM_DURATIONS = {
    "premium_1w": timedelta(weeks=1),
    "premium_2w": timedelta(weeks=2),
    "premium_1m": timedelta(days=30),
    "premium_3m": timedelta(days=90),
}


async def get_or_create_user(tg_id: int, username: str | None, ref_code_used: str | None = None) -> asyncpg.Record:
    pool = await get_pool()
    async with pool.acquire() as conn:
        user = await conn.fetchrow("SELECT * FROM users WHERE tg_id = $1", tg_id)
        if user:
            return user

        ref_code = secrets.token_urlsafe(8)
        referred_by = None

        if ref_code_used:
            referrer = await conn.fetchrow("SELECT tg_id FROM users WHERE ref_code = $1", ref_code_used)
            if referrer:
                referred_by = ref_code_used

        user = await conn.fetchrow(
            """
            INSERT INTO users (tg_id, username, ref_code, referred_by)
            VALUES ($1, $2, $3, $4)
            RETURNING *
            """,
            tg_id, username, ref_code, referred_by,
        )
        return user


async def get_user(tg_id: int) -> asyncpg.Record | None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow("SELECT * FROM users WHERE tg_id = $1", tg_id)


async def deduct_message(tg_id: int) -> bool:
    """Returns False if balance is 0. Premium users are never blocked."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.fetchrow(
            """
            UPDATE users SET messages_sent = messages_sent + 1,
                balance = CASE WHEN is_premium THEN balance ELSE balance - 1 END
            WHERE tg_id = $1 AND (is_premium OR balance > 0)
            RETURNING balance
            """,
            tg_id,
        )
        return result is not None


async def add_balance(tg_id: int, amount: int) -> None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET balance = balance + $1 WHERE tg_id = $2",
            amount, tg_id,
        )


async def get_user_stats(tg_id: int) -> dict:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT
                u.balance,
                u.is_premium,
                u.dialogs_created,
                u.messages_sent,
                (SELECT COUNT(*) FROM conversations c JOIN users uu ON c.user_id = uu.id WHERE uu.tg_id = $1) as total_dialogs
            FROM users u WHERE u.tg_id = $1
            """,
            tg_id,
        )
        return dict(row) if row else {}


async def get_referral_stats(tg_id: int) -> dict:
    pool = await get_pool()
    async with pool.acquire() as conn:
        user = await conn.fetchrow("SELECT ref_code FROM users WHERE tg_id = $1", tg_id)
        if not user:
            return {}
        ref_code = user["ref_code"]
        invited = await conn.fetchval(
            "SELECT COUNT(*) FROM users WHERE referred_by = $1", ref_code
        )
        earned = await conn.fetchval(
            """
            SELECT COALESCE(SUM(p.messages_added / 2), 0)
            FROM purchases p
            JOIN users u ON p.user_id = u.id
            WHERE u.referred_by = $1
            """,
            ref_code,
        )
        return {"ref_code": ref_code, "invited": invited, "earned": earned or 0}


async def get_all_scenarios() -> list[asyncpg.Record]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch("SELECT * FROM scenarios ORDER BY sort_order")


async def create_conversation(tg_id: int, scenario_id: int) -> int:
    pool = await get_pool()
    async with pool.acquire() as conn:
        user = await conn.fetchrow("SELECT id FROM users WHERE tg_id = $1", tg_id)
        conv = await conn.fetchrow(
            "INSERT INTO conversations (user_id, scenario_id) VALUES ($1, $2) RETURNING id",
            user["id"], scenario_id,
        )
        await conn.execute(
            "UPDATE users SET dialogs_created = dialogs_created + 1 WHERE tg_id = $1",
            tg_id,
        )
        return conv["id"]


async def get_conversation_history(conversation_id: int, limit: int = 20) -> list[dict]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT role, content FROM messages WHERE conversation_id = $1 ORDER BY created_at DESC LIMIT $2",
            conversation_id, limit,
        )
        return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]


async def save_message(conversation_id: int, role: str, content: str) -> None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO messages (conversation_id, role, content) VALUES ($1, $2, $3)",
            conversation_id, role, content,
        )


async def record_purchase(tg_id: int, purchase_type: str, messages_added: int, stars_paid: int) -> None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        user = await conn.fetchrow("SELECT id, referred_by FROM users WHERE tg_id = $1", tg_id)
        await conn.execute(
            "INSERT INTO purchases (user_id, type, messages_added, stars_paid) VALUES ($1, $2, $3, $4)",
            user["id"], purchase_type, messages_added, stars_paid,
        )
        await conn.execute(
            "UPDATE users SET balance = balance + $1 WHERE tg_id = $2",
            messages_added, tg_id,
        )
        # Activate premium if this is a premium purchase
        duration = PREMIUM_DURATIONS.get(purchase_type)
        if duration:
            await conn.execute(
                """
                UPDATE users
                SET is_premium = TRUE,
                    premium_until = GREATEST(COALESCE(premium_until, NOW()), NOW()) + $1
                WHERE tg_id = $2
                """,
                duration, tg_id,
            )
        # Give referrer bonus (50% of messages added)
        if user["referred_by"]:
            bonus = messages_added // 2
            if bonus > 0:
                await conn.execute(
                    "UPDATE users SET balance = balance + $1 WHERE ref_code = $2",
                    bonus, user["referred_by"],
                )
