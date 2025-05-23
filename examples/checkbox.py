import asyncio

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

import config
from aiogramx.checkbox import Checkbox

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()

Checkbox.register(dp)


@dp.message(Command("checkbox"))
async def checkbox_handler(m: Message):
    async def on_select(cq: CallbackQuery, data: dict):
        await cq.message.edit_text(
            text=str("".join([f"{k}: {v['flag']}\n" for k, v in data.items()]))
        )

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
    }

    c = Checkbox(
        options=options,
        on_select=on_select,
    )
    await m.answer(text="Checkbox Demo", reply_markup=await c.render_kb())


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
