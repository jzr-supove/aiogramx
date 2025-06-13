import asyncio
from aiogram import F, Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message

from aiogramx import ReplyKeyboardMeta
from config import BOT_TOKEN


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


class ExampleKB(
    metaclass=ReplyKeyboardMeta,
    resize_keyboard=True,
    input_field_placeholder="...",
    is_persistent=True,
    one_time_keyboard=True,
    selective=True,
):
    B1 = "Button 1"
    B2 = "Button 2"
    B3 = "Button 3"
    B4 = "Button 4"
    HELP = "🆘 Help"

    __LAYOUT__ = [
        [B1, B2],
        [HELP],
        [B4, B3],
    ]


@dp.message(Command("keyboard"))
async def reply_keyboard(m: Message):
    await m.answer("📋 Reply Keyboard Example", reply_markup=ExampleKB.kb)


@dp.message(F.text.in_(ExampleKB))
async def example_kb_handler(m: Message):
    if m.text == ExampleKB.B1:
        await m.answer("B1 is pressed!")

    elif m.text == ExampleKB.B2:
        await m.answer(f"'{ExampleKB.B2}' is pressed!")

    elif m.text == ExampleKB.B3:
        await m.answer(f"{ExampleKB.B3!r} is pressed!")

    elif m.text == ExampleKB.B4:
        await m.answer("B4 is pressed!")

    elif m.text == ExampleKB.HELP:
        await m.answer("Help message")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
