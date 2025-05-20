from typing import Union

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton

import string
import random


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
