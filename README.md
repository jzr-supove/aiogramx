# AiogramX

Widgets and tools for bots built with Aiogram. Supports inline keyboards, paginators, and other helper UI components.


## Time Selectors

### Usage Example

```python
from aiogramx.time import TimeSelectorGrid


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
```

### Other example
```python
from aiogramx.time import TimeSelectorModern

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
```

## Paginator

### Basic Example
```python
from aiogramx.pagination import Paginator

Paginator.register(dp)

def get_buttons():
    return [
        InlineKeyboardButton(text=f"Element {i}", callback_data=f"elem {i}")
        for i in range(10_000)
    ]


@dp.message(Command("pages"))
async def pages_handler(m: Message):
    pg = Paginator(per_page=15, per_row=2, data=get_buttons())
    await m.answer(text="Pagination Demo", reply_markup=await pg.render_kb())


@dp.callback_query(F.data.startswith("elem "))
async def handle_buttons(c: CallbackQuery):
    await c.message.edit_text(text=f"Selected elem with callback '{c.data}'")
```

### Example with `on_select` and `on_back` callback functions:
```python
from aiogramx.pagination import Paginator

Paginator.register(dp)

def get_buttons():
    return [
        InlineKeyboardButton(text=f"Element {i}", callback_data=f"elem {i}")
        for i in range(10_000)
    ]


@dp.message(Command("pages"))
async def pages_handler(m: Message):
    async def on_select(c: CallbackQuery, data: str):
        await c.answer(text=f"Selected '{data}'")

    async def on_back(c: CallbackQuery):
        await c.message.edit_text("Ok")

    pg = Paginator(
        per_page=15, per_row=2, data=get_buttons(), on_select=on_select, on_back=on_back
    )
    await m.answer(text="Pagination Demo", reply_markup=await pg.render_kb())
```

### Example using lazy functions
```python
from aiogramx.pagination import Paginator

Paginator.register(dp)

async def get_buttons_lazy(cur_page: int, per_page: int) -> list[InlineKeyboardButton]:
    results = fetch_results_from_somewhere(cur_page, per_page)

    return [
        InlineKeyboardButton(text=row["value"], callback_data=f"id|{row['id']}")
        for row in results
    ]


async def get_count_lazy() -> int:
    async with pool.acquire() as conn:
        return await conn.fetchval("SELECT COUNT(*) FROM test_data")


async def handle_data_select(c: CallbackQuery, data: str):
    await c.message.edit_text(text=f"Selected callback '{data}'")


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
```