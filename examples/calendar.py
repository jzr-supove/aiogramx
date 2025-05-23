import asyncio
from datetime import date

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from asyncpg.pgproto.pgproto import timedelta

import config
from aiogramx.calendar import Calendar

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()

Calendar.register(dp)


@dp.message(Command("calendar"))
async def calendar_handler(m: Message):
    async def on_select(cq: CallbackQuery, date_obj: date):
        await cq.message.edit_text(text=str(date_obj))

    async def on_back(cq: CallbackQuery):
        await cq.message.edit_text(text="Canceled")

    c = Calendar(
        max_range=timedelta(weeks=12),
        show_quick_buttons=True,
        on_select=on_select,
        on_back=on_back,
    )
    await m.answer(text="Calendar Demo", reply_markup=await c.render_kb())


# @dp.callback_query(Calendar.filter())
# async def handle_calendar_callback(q: CallbackQuery, callback_data: Calendar.cb):
#     c = Calendar()
#     res = await c.process_cb(q, callback_data)
#
#     if not res.completed:
#         return
#
#     if res.chosen_date:
#         await q.message.answer(text=f"Chosen date: {res.chosen_date}")
#     else:
#         await q.message.edit_text(text="Pressed Back")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
