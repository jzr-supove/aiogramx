import asyncio
from typing import Any

from aiogram import Bot, Dispatcher, F
from aiogram.types import CallbackQuery, Message

from aiogramx.time import TimeSelectorModern, TimeSelectorGrid

bot = Bot(token="<BOT_TOKEN>")
dp = Dispatcher()


ts_modern = TimeSelectorModern(
    allow_future_only=True, past_time_warning="Selecting past time not allowed!"
)


@dp.message(F.text == "/modern")
async def modern_kb_handler(m: Message):
    await m.answer(
        text="Time Selector Modern",
        reply_markup=ts_modern.render_kb(offset_minutes=5),
    )


@dp.callback_query(TimeSelectorModern.filter())
async def time_selector_handler(c: CallbackQuery, callback_data: Any) -> None:
    result = await ts_modern.handle_cb(query=c, data=callback_data)

    if not result.completed:
        return  # still waiting for user to select time

    if result.chosen_time:
        await c.message.edit_text(
            text=f"Time selected: {result.chosen_time.strftime('%H:%M')}"
        )
    else:
        await c.message.edit_text(text="Operation Canceled")


@dp.message(F.text == "/grid")
async def grid_kb_handler(m: Message):
    await m.answer(
        text="Time Selector Grid", reply_markup=TimeSelectorGrid().render_kb()
    )


@dp.callback_query(TimeSelectorGrid.filter())
async def time_selector_grid_handler(c: CallbackQuery, callback_data: Any) -> None:
    ts = TimeSelectorGrid(allow_future_only=True)
    result = await ts.handle_cb(query=c, data=callback_data)

    if not result.completed:
        return

    if result.chosen_time:
        await c.message.edit_text(text=f"Time selected: {result.chosen_time}")
    else:
        await c.message.edit_text(text="Operation Canceled")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
