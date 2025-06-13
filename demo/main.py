import asyncio
from datetime import date, timedelta, time

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command, CommandObject
from aiogram.filters.callback_data import CallbackData
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton, BotCommand

from aiogramx import (
    Checkbox,
    Calendar,
    TimeSelectorGrid,
    TimeSelectorModern,
    Paginator,
    ReplyKeyboardMeta,
)
from config import BOT_TOKEN, HELP_ARGS
from helper import extract_pager_data, extract_time_selector_data, boolmoji, langmoji


bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

# Register AiogramX widgets
Checkbox.register(dp)
Calendar.register(dp)
Paginator.register(dp)
TimeSelectorGrid.register(dp)


commands = {
    "start": "Start the bot",
    "help": "Show help message",
    "pages": "Pagination Demo",
    "checkbox": "Checkbox Demo",
    "calendar": "Calendar Demo",
    "time": "Time Selector Demo",
    "keyboard": "Reply Keyboard Demo",
}

bot_commands = [BotCommand(command=k, description=v) for k, v in commands.items()]


# When using Paginator with on_select callback, Paginator will wrap the buttons inside its own CallbackData
# So, in order to avoid collisions, you have to use a CallbackData class with `sep` other than ':'
class TestDataCB(CallbackData, prefix="test_data", sep="!"):
    id: int


@dp.message(Command("start"))
async def start_handler(m: Message):
    await m.answer(
        "Welcome to AiogramX Demo Bot!\n\nUse /help to see available commands."
    )


@dp.message(Command("help"))
async def help_handler(m: Message):
    help_text = "📋 <b>Available commands:</b>\n\n"
    for cmd in bot_commands:
        help_text += f"/{cmd.command} - {cmd.description}\n"

    help_text += "\n" + HELP_ARGS
    await m.answer(help_text)


@dp.message(Command("checkbox"))
async def start_checkbox_demo(m: Message, command: CommandObject):
    async def on_select(cq: CallbackQuery, data: dict):
        selected = [k for k, v in data.items() if v["flag"]]
        summary = "✅ You will receive:\n" + "\n".join(f"• {s}" for s in selected)
        await cq.message.edit_text(summary)

    async def on_back(cq: CallbackQuery):
        await cq.message.edit_text("✔️ Notification setup canceled")

    options = {
        "news": {"text": "📰 News", "flag": True},
        "games": {"text": "🎮 Game Invites", "flag": False},
        "releases": {"text": "🛠 Releases", "flag": True},
        "beta": {"text": "🧪 Beta Access", "flag": False},
    }

    ch = Checkbox(
        options=options, on_select=on_select, on_back=on_back, lang=command.args
    )
    await m.answer(
        "<b>✅ Checkbox Demo</b>\n\nSelect your notification preferences:",
        reply_markup=ch.render_kb(),
    )


@dp.message(Command("calendar"))
async def start_calendar_demo(m: Message, command: CommandObject):
    async def on_select(cq: CallbackQuery, date_obj: date):
        await cq.message.edit_text(
            text=f"🗓 Selected date: <b>{date_obj.strftime('%Y-%m-%d')}</b>"
        )

    async def on_back(cq: CallbackQuery):
        await cq.message.edit_text(text="✔️ Date selection canceled")

    c = Calendar(
        max_range=timedelta(weeks=12),
        show_quick_buttons=True,
        on_select=on_select,
        on_back=on_back,
        lang=command.args,
    )
    await m.answer(text="🗓 Calendar Demo", reply_markup=c.render_kb())


@dp.message(Command("pages"))
async def start_pages_demo(m: Message, command: CommandObject):
    lang, per_page, per_row = extract_pager_data(command.args)

    def get_buttons():
        return [
            InlineKeyboardButton(
                text=f"Item {i}", callback_data=TestDataCB(id=i).pack()
            )
            for i in range(10_000)
        ]

    async def handle_data_select(c: CallbackQuery, data: str):
        await c.message.edit_text(
            text=f"☑️ Selected element with callback data <code>{data}</code>"
        )

    async def handle_back(c: CallbackQuery):
        await c.message.edit_text("✔️ Pagination closed")

    try:
        p = Paginator(
            per_page=per_page,
            per_row=per_row,
            data=get_buttons(),
            on_select=handle_data_select,
            on_back=handle_back,
            lang=lang,
        )

        await m.answer(text="📖 Pagination Demo", reply_markup=await p.render_kb())
    except ValueError as e:
        await m.answer(f"❌ <b>{e}</b>")


@dp.message(Command("time"))
async def start_time_selector_demo(m: Message, command: CommandObject):
    lang, ts_type, future_only, carry_over = extract_time_selector_data(command.args)

    async def on_select(cq: CallbackQuery, time_obj: time):
        await cq.message.edit_text(text=f"⏰ Selected time: <b>{time_obj}</b>")
        await cq.answer()

    async def on_back(cq: CallbackQuery):
        await cq.message.edit_text(text="✔️ Time selection canceled")
        await cq.answer()

    t_class = TimeSelectorGrid if ts_type == "grid" else TimeSelectorModern
    ts = t_class(
        allow_future_only=future_only,
        carry_over=carry_over,
        on_select=on_select,
        on_back=on_back,
        lang=lang,
        done_button_text="✅ Done",
        back_button_text="🔙 Cancel",
    )

    text = (
        f"<b>⏰ Time Selector Demo</b>\n\n"
        f"Settings:\n"
        f"- Type: <b>{ts_type.title()}</b>\n"
        f"- Allow future only: {boolmoji(future_only)}\n"
        f"- Carry over: {boolmoji(carry_over)}\n"
        f"- Language: {langmoji(lang)}"
    )
    await m.answer(text=text, reply_markup=ts.render_kb())


class TestRKB(metaclass=ReplyKeyboardMeta, input_field_placeholder="👇 Demo buttons"):
    GREET = "👋 Say Hello"
    ASK = "❓ Ask Something"
    JOKE = "😂 Tell a Joke"
    CANCEL = "❌ Cancel"
    HELP = "🆘 Help"

    __LAYOUT__ = [
        [GREET, ASK],
        [HELP],
        [JOKE, CANCEL],
    ]


@dp.message(Command("keyboard"))
async def reply_keyboard_demo(m: Message):
    await m.answer("📋 Reply Keyboard Demo", reply_markup=TestRKB.kb)


@dp.message(F.text.in_(TestRKB))
async def test_kb_handler(m: Message):
    if m.text == TestRKB.GREET:
        await m.answer("Hello there! 👋")

    elif m.text == TestRKB.ASK:
        await m.answer("Sure, what do you want to ask?")

    elif m.text == TestRKB.JOKE:
        joke = "Why did the Python programmer go hungry? Because he couldn't 'byte'!"
        await m.answer(joke)

    elif m.text == TestRKB.CANCEL:
        await m.answer("👌 Keyboard is closed", reply_markup=TestRKB.remove)

    elif m.text == TestRKB.HELP:
        await m.answer("🔘 Use the buttons to interact with the bot!")


async def main():
    await bot.set_my_commands(bot_commands)
    print(f"✅ Demo bot @{(await bot.me()).username} is up and running!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
