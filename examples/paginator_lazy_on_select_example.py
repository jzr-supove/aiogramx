import asyncio

import asyncpg
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton

from config import BOT_TOKEN, POSTGRES_URL
from aiogramx import Paginator


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

pg_pool = asyncpg.create_pool(
    dsn=POSTGRES_URL, max_size=500, max_inactive_connection_lifetime=5
)

Paginator.register(dp)


async def get_buttons_lazy(cur_page: int, per_page: int) -> list[InlineKeyboardButton]:
    async with pg_pool.acquire() as conn:
        results = await conn.fetch(
            "SELECT * FROM test_data OFFSET $1 LIMIT $2",
            (cur_page - 1) * per_page,
            per_page,
        )

    return [
        InlineKeyboardButton(text=row["value"], callback_data=f"id|{row['id']}")
        for row in results
    ]


async def get_count_lazy() -> int:
    async with pg_pool.acquire() as conn:
        return await conn.fetchval("SELECT COUNT(*) FROM test_data")


async def handle_data_select(c: CallbackQuery, data: str):
    button_text = "null"
    for row in c.message.reply_markup.inline_keyboard:
        for b in row:
            if b.callback_data == c.data:
                button_text = b.text

    await c.message.edit_text(
        text=f"Selected callback '{data}' (button '{button_text}')"
    )


async def handle_back(c: CallbackQuery):
    await c.message.edit_text("Pagination closed")


@dp.message(Command("pages"))
async def pages_handler(m: Message):
    p = Paginator(
        per_page=11,
        per_row=3,
        lazy_data=get_buttons_lazy,
        lazy_count=get_count_lazy,
        on_select=handle_data_select,
        on_back=handle_back,
    )

    await m.answer(text="Pagination Demo", reply_markup=await p.render_kb())


async def main():
    pg_pool._loop = asyncio.get_event_loop()
    await pg_pool
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
