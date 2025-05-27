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


@dp.message(Command("checkbox2"))
async def checkbox2_handler(m: Message):
    ch = Checkbox(["Option 1", "Option 2", "Option 3"])
    await m.answer(text="Checkbox Demo 2", reply_markup=await ch.render_kb())


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
