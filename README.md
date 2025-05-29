# AiogramX

[![PyPI version](https://img.shields.io/pypi/v/aiogramx.svg)](https://pypi.org/project/aiogramx/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)
[![Downloads](https://static.pepy.tech/personalized-badge/aiogramx?period=month&units=international_system&left_color=gray&right_color=blue&left_text=downloads/month)](https://pepy.tech/project/aiogramx)
[![GitHub stars](https://img.shields.io/github/stars/jzr-supove/aiogramx?style=social)](https://github.com/jzr-supove/aiogramx)

<table>
<tr>
<td width="60%">
    
AiogramX is a modular collection of widgets and tools for building advanced Telegram bots using [Aiogram](https://aiogram.dev/). It simplifies the creation of user interfaces with inline keyboards, time selectors, calendars, paginators, and checkboxes — all with a clean API and optional callback handling.

---

#### Quick Links

- 📦 [PyPI Package](https://pypi.org/project/aiogramx/)
- 📚 [Documentation](https://github.com/jzr-supove/aiogramx/wiki)
- 🐛 [Issue Tracker](https://github.com/jzr-supove/aiogramx/issues)
- 📬 [Submit Pull Request](https://github.com/jzr-supove/aiogramx/pulls)
- 🤖 [Live Demo Bot](https://t.me/aiogramx_demobot?start=github)

</td>

<td align="right">
    <img src="https://i.imgur.com/6jxmiEl.png" alt="AiogramX Logo" width="500px"/>
</td>
</tr>
</table>

---


## ✨ Features
- Paginator with lazy loading support
- Interactive calendar with date selection
- Versatile checkbox component
- Time selection widgets (grid and modern)
- Easy integration and custom callbacks
- Full compatibility with aiogram 3.x


## 🚀 Why AiogramX?

AiogramX is designed with **performance and scalability** in mind. Unlike other widget libraries, it avoids common architectural pitfalls that can degrade your bot’s performance over time.

### ✅ Efficient Callback Handling

Most other libraries create **a new callback handler per widget instance**, which leads to:
- 📈 **Handler bloat**: Thousands of handlers pile up as users interact with widgets
- 🐢 **Slowdowns**: Aiogram has to iterate over a large handler list on every callback
- 🗑️ **Memory waste**: Unused handlers remain registered, even after widgets are discarded 

### 🧠 AiogramX does it differently

AiogramX uses an internal **LRU (Least Recently Used) storage** mechanism (from [FlipCache](https://github.com/jzr-supove/flipcache)) to manage widget instances:
- 🔁 **Single callback handler per widget type** (e.g. TimeSelector, Paginator) 
- 🧹 **Old widget instances are automatically evicted** from memory after a limit (default: 1000)
- 🧵 **Cleaner, more predictable handler lifecycle**
- ⚡ **Improved performance** and **faster dispatching** of callbacks

This architecture keeps your bot responsive, even under heavy usage.


## 📦 Installation
```bash
pip install aiogramx
```

## 📚 Components

### 📄 Paginator

#### Basic usage example
```python
from aiogramx import Paginator

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

#### Example with `on_select` and `on_back` callback functions

```python
from aiogramx import Paginator

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

#### Example using lazy functions
```python
from aiogramx import Paginator

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

### 📅 Calendar

#### Usage example

```python
from aiogramx import Calendar

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
```

### ☑️ Checkbox

#### Basic usage

```python
from aiogramx import Checkbox

Checkbox.register(dp)

@dp.message(Command("checkbox2"))
async def checkbox2_handler(m: Message):
    ch = Checkbox(["Option 1", "Option 2", "Option 3"])
    await m.answer(text="Checkbox Demo 2", reply_markup=await ch.render_kb())
```

#### Advanced usage with callback functions

```python
from aiogramx import Checkbox

Checkbox.register(dp)

@dp.message(Command("checkbox"))
async def checkbox_handler(m: Message):
    async def on_select(cq: CallbackQuery, data: dict):
        flag_map = {True: "✅", False: "❌"}

        await cq.message.edit_text(
            text=str(
                "".join([f"{k}: {flag_map[v['flag']]}\n" for k, v in data.items()])
            )
        )

    async def on_back(cq: CallbackQuery):
        await cq.message.edit_text(text="You pressed the back button!")

    options = {
        "video_note": {
            "text": "🎞",
            "flag": True,
        },
        "voice": {
            "text": "🔉",
            "flag": False,
        },
        "test": None,
        "other": {},
    }

    ch = Checkbox(
        options=options,
        on_select=on_select,
        on_back=on_back,
    )
    await m.answer(text="Checkbox Demo", reply_markup=await ch.render_kb())
```

### ⏰  Time Selectors

#### Basic usage

```python
from aiogramx import TimeSelectorGrid

TimeSelectorGrid.register(dp)

@dp.message(Command("grid"))
async def grid_kb_handler(m: Message):
    ts_grid = TimeSelectorGrid()
    await m.answer(text="Time Selector Grid", reply_markup=ts_grid.render_kb())
```

#### Advanced usage with callback functions

```python
from aiogramx import TimeSelectorModern

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
```

For more usage examples and details, see [examples](./examples)

## 🧪 Contributing
Contributions are welcome! If you'd like to add new widgets or improve existing ones, feel free to open issues or submit pull requests.

## 📜 License
This project is licensed under the MIT License. See the LICENSE file for more information.
