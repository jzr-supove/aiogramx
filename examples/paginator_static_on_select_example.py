import asyncio

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton

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
    async def on_select(c: CallbackQuery, data: str):
        await c.answer(text=f"Selected '{data}'")

    async def on_back(c: CallbackQuery):
        await c.message.edit_text("Ok")

    pg = Paginator(
        per_page=15, per_row=2, data=get_buttons(), on_select=on_select, on_back=on_back
    )
    await m.answer(text="Pagination Demo", reply_markup=await pg.render_kb())


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
