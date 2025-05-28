import asyncio
from datetime import date

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from asyncpg.pgproto.pgproto import timedelta

from config import BOT_TOKEN
from aiogramx import Calendar

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

Calendar.register(dp)


@dp.message(Command("calendar"))
async def calendar_handler(m: Message):
    async def on_select(cq: CallbackQuery, date_obj: date):
        await cq.message.edit_text(
            text="Selected date: " + date_obj.strftime("%Y-%m-%d")
        )

    async def on_back(cq: CallbackQuery):
        await cq.message.edit_text(text="Canceled")

    c = Calendar(
        max_range=timedelta(weeks=12),
        show_quick_buttons=True,
        on_select=on_select,
        on_back=on_back,
    )
    await m.answer(text="Calendar Demo", reply_markup=await c.render_kb())


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
