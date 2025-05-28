import asyncio

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardButton, CallbackQuery

from config import BOT_TOKEN
from aiogramx import Paginator

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


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


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
