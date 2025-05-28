import asyncio
from typing import Any

from aiogram.filters import Command
from aiogram.types import Message

from aiogram import Bot, Dispatcher
from aiogram.types import CallbackQuery

from config import BOT_TOKEN
from aiogramx import TimeSelectorGrid

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(Command("grid"))
async def grid_kb_handler(m: Message):
    await m.answer(
        text="Time Selector Grid", reply_markup=TimeSelectorGrid().render_kb()
    )


# If you want, you can have full control over the callback data handling
# Just register your own callback query handler like this, instead of doing TimeSelectorGrid.register(dp)


@dp.callback_query(TimeSelectorGrid.filter())
async def time_selector_grid_handler(c: CallbackQuery, callback_data: Any) -> None:
    ts = TimeSelectorGrid.from_cb(callback_data)
    if not ts:
        await c.message.delete()
        await c.answer(ts.get_expired_text())
        return

    result = await ts.process_cb(query=c, data=callback_data)

    if not result.completed:
        return  # still waiting for user to select time

    elif result.chosen_time:
        await c.message.edit_text(
            text=f"Time selected: {result.chosen_time.strftime('%H:%M')}"
        )
    else:
        await c.message.edit_text(text="Operation Canceled")

    await c.answer()


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
