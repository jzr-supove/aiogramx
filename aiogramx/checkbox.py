from aiogram.filters.callback_data import CallbackData
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from aiogramx.base import WidgetBase
from aiogramx.utils import ibtn

from typing import Dict, TypedDict, Callable, Optional, Awaitable, Union, List, Any


class PartialOptionEntry(TypedDict, total=False):
    text: str
    flag: bool


OptionsInput = Union[
    List[str],
    Dict[str, Optional[Dict[str, Any]]],
]


class CheckboxCB(CallbackData, prefix="aiogramx_chx"):
    action: str
    arg: str = ""
    key: str = ""


class Checkbox(WidgetBase[CheckboxCB, "Checkbox"]):
    _cb = CheckboxCB

    def __init__(
        self,
        options: Any,
        can_select_none: bool = False,
        on_select: Optional[Callable[[CallbackQuery, dict], Awaitable[None]]] = None,
        on_back: Optional[Callable[[CallbackQuery], Awaitable[None]]] = None,
    ):
        self._options: Dict[str, PartialOptionEntry] = {}

        if isinstance(options, list):
            for key in options:
                self._options[key] = {"text": key, "flag": False}

        elif isinstance(options, dict):
            for key, val in options.items():
                if val is None:
                    val = {}
                self._options[key] = {
                    "text": val.get("text", key),
                    "flag": bool(val.get("flag", False)),
                }

        if not isinstance(options, (dict, list)):
            raise TypeError("Expected list of keys or dict[str, dict] as options")

        self._can_select_none = can_select_none
        self.on_select = on_select
        self.on_back = on_back

        super().__init__()

    @classmethod
    def get_expired_text(cls) -> str:
        return "This checkbox keyboard is expired"

    def is_selected_any(self) -> bool:
        for o in self._options.values():
            if o["flag"] is True:
                return True
        return False

    async def process_cb(self, c: CallbackQuery, data: CheckboxCB):
        if data.action == "IGNORE":
            await c.answer(cache_time=60)

        if data.action == "CHECK":
            self._options[data.arg]["flag"] = not self._options[data.arg]["flag"]
            await c.message.edit_reply_markup(reply_markup=await self.render_kb())

        elif data.action == "DONE":
            if not self._can_select_none and not self.is_selected_any():
                await c.answer("At least one option must be selected")
                return

            if self.on_select:
                await self.on_select(c, self._options)
            else:
                await c.message.edit_text(str(self._options))

    async def render_kb(self):
        kb = InlineKeyboardBuilder()
        for k, v in self._options.items():
            kb.add(
                ibtn(
                    text=v["text"],
                    cb=self._cb(action="IGNORE", key=self._key),
                ),
                ibtn(
                    text="✅" if v["flag"] else "[  ]",
                    cb=self._cb(action="CHECK", arg=k, key=self._key),
                ),
            )
        kb.adjust(2)
        kb.row(ibtn("☑️ Done", cb=self._cb(action="DONE", key=self._key)))
        return kb.as_markup()
