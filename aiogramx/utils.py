import inspect
from contextlib import asynccontextmanager
from typing import Union, Optional, Callable, Awaitable

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton

import string
import random


ExceptionHandler = Callable[[Exception], Union[None, Awaitable[None]]]

# Character set: A-Z, a-z, 0-9, symbols
punctuation = r"!#$%&*+,-./;<=>?@[\]^_{}~"
CHARSET = string.ascii_letters + string.digits + punctuation


def gen_key(existing: dict, length: int = 5) -> str:
    while True:
        key = "".join(random.choice(CHARSET) for _ in range(length))
        if key not in existing:
            return key


def ibtn(text: str, cb: Union[CallbackData, str]) -> InlineKeyboardButton:
    if isinstance(cb, CallbackData):
        cb = cb.pack()
    return InlineKeyboardButton(text=text, callback_data=cb)


@asynccontextmanager
async def silent_fail(on_exception: Optional[ExceptionHandler] = None):
    try:
        yield
    except Exception as e:
        if on_exception:
            result = on_exception(e)
            if inspect.isawaitable(result):
                await result
