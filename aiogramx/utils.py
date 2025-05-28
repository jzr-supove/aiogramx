import inspect
from contextlib import asynccontextmanager
from typing import Union, Optional, Callable, Awaitable, Literal

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton

import string
import random


ExceptionHandler = Callable[[Exception], Union[None, Awaitable[None]]]
LangCode = Literal["en", "ru", "uz"]
SUPPORTED_LANGS = {"en", "ru", "uz"}

# Character set: A-Z, a-z, 0-9, symbols
PUNCTUATION = r"!#$%&*+,-./;<=>?@[\]^_{}~"
CHARSET = string.ascii_letters + string.digits + PUNCTUATION


def fallback_lang(lang: Optional[LangCode]) -> LangCode:
    """
    Returns a fallback language code if the provided one is not supported.

    Args:
        lang (Optional[LangCode]): The language code to check.

    Returns:
        LangCode: A supported language code, defaults to 'en' if the input is None or unsupported.
    """
    return lang if lang in SUPPORTED_LANGS else "en"


def gen_key(existing: dict, length: int = 5) -> str:
    """Generates a unique key of specified length that does not exist in the provided dictionary."""
    while True:
        key = "".join(random.choice(CHARSET) for _ in range(length))
        if key not in existing:
            return key


def ibtn(text: str, cb: Union[CallbackData, str]) -> InlineKeyboardButton:
    """Generates an InlineKeyboardButton with the specified text and callback data."""
    if isinstance(cb, CallbackData):
        cb = cb.pack()
    return InlineKeyboardButton(text=text, callback_data=cb)


@asynccontextmanager
async def silent_fail(on_exception: Optional[ExceptionHandler] = None):
    """Asynchronous context manager that suppresses exceptions and optionally handles them with a callback."""
    try:
        yield
    except Exception as e:
        if on_exception:
            result = on_exception(e)
            if inspect.isawaitable(result):
                await result
