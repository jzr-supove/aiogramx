# AiogramX

Widgets and tools for bots built with Aiogram. Supports inline keyboards, paginators, and other helper UI components.

> Minimal placeholder release to reserve the name.
>
> This package will provide helpful widgets and builders for Aiogram bots, including calendar keyboards, paginators, and data selectors for Aiogram 2.x and 3.x.


## Time Selectors

### Usage Example

```python
import asyncio
from typing import Any

from aiogram import Bot, Dispatcher, F
from aiogram.types import CallbackQuery, Message

from aiogramx.time import TimeSelectorGrid


bot = Bot(token="<API_TOKEN>")
dp = Dispatcher()


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
        return  # still waiting for user to select time

    if result.chosen_time:
        await c.message.edit_text(
            text=f"Time selected: {result.chosen_time.strftime('%H:%M')}"
        )
    else:
        await c.message.edit_text(text="Operation Canceled")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
```

### Other example
```python
import asyncio
from typing import Any
from aiogram import Bot, Dispatcher, F
from aiogram.types import CallbackQuery, Message
from aiogramx.time import TimeSelectorModern


bot = Bot(token="<API_TOKEN>")
dp = Dispatcher()

ts_modern = TimeSelectorModern(
    allow_future_only=True, 
    past_time_warning="Selecting past time not allowed!"
)


@dp.message(F.text == "/modern")
async def modern_kb_handler(m: Message):
    await m.answer(
        text="Time Selector Modern",
        reply_markup=ts_modern.render_kb(offset_minutes=5),
    )

    
@dp.callback_query(ts_modern.filter())
async def time_selector_handler(c: CallbackQuery, callback_data: Any) -> None:
    result = await ts_modern.handle_cb(query=c, data=callback_data)

    if not result.completed:
        return

    if result.chosen_time:
        await c.message.edit_text(
            text=f"Time selected: {result.chosen_time.strftime('%H:%M')}"
        )
    else:
        await c.message.edit_text(text="Operation Canceled")

if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))
```