import asyncio
import time

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from config import BOT_TOKEN
from aiogramx import TimeSelectorModern, TimeSelectorGrid

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Registering one of the TimeSelector classes is enough, no need to register both
TimeSelectorModern.register(dp)


@dp.message(Command("modern"))
async def modern_ts_handler(m: Message):
    async def on_select(c: CallbackQuery, time_obj: time):
        await c.message.edit_text(text=f"Time selected: {time_obj.strftime('%H:%M')}")
        await c.answer()

    async def on_back(c: CallbackQuery):
        await c.message.edit_text(text="Operation Canceled")
        await c.answer()

    ts_modern = TimeSelectorModern(
        allow_future_only=True,
        on_select=on_select,
        on_back=on_back,
        lang=m.from_user.language_code,
    )

    await m.answer(
        text="Time Selector Modern",
        reply_markup=ts_modern.render_kb(offset_minutes=5),
    )


@dp.message(Command("grid"))
async def grid_kb_handler(m: Message):
    ts_grid = TimeSelectorGrid()
    await m.answer(text="Time Selector Grid", reply_markup=ts_grid.render_kb())


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
