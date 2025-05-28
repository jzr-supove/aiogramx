import json
from dataclasses import dataclass

from aiogram.filters.callback_data import CallbackData
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from aiogramx.base import WidgetBase
from aiogramx.utils import ibtn, fallback_lang, LangCode

from typing import Dict, TypedDict, Callable, Optional, Awaitable, Union, List


_TEXTS = {
    "en": {
        "at_least_one": "At least one option must be selected!",
        "done": "☑️ Done",
        "back": "🔙 Back",
    },
    "ru": {
        "at_least_one": "Должен быть выбран хотя бы один вариант!",
        "done": "☑️ Готово",
        "back": "🔙 Назад",
    },
    "uz": {
        "at_least_one": "Kamida bitta variant tanlanishi kerak!",
        "done": "☑️ Tayyor",
        "back": "🔙 Orqaga",
    },
}


class OptionMeta(TypedDict, total=False):
    """
    Represents metadata for an individual checkbox option.

    Attributes:
        text (str): Display text for the option.
        flag (bool): Whether the option is currently selected.
    """

    text: str
    flag: bool


OptionsInput = Union[
    List[str],
    Dict[str, Optional[OptionMeta]],
]


@dataclass
class CheckboxResult:
    """
    Represents the result of a checkbox interaction.

    Attributes:
        completed (bool): Whether the interaction is complete (e.g., user clicked Done or Back).
        options (Optional[Dict[str, OptionMeta]]): The final state of the options if applicable.
    """

    completed: bool
    options: Optional[Dict[str, OptionMeta]] = None


class CheckboxCB(CallbackData, prefix="aiogramx_chx"):
    """
    Defines the callback data structure for checkbox interactions.

    Attributes:
        action (str): The type of action (e.g., CHECK, DONE, BACK, IGNORE).
        arg (str): Argument related to the action (usually the option key).
        key (str): A unique identifier for the widget instance.
    """

    action: str
    arg: str = ""
    key: str = ""


class Checkbox(WidgetBase[CheckboxCB, "Checkbox"]):
    """
    A widget for rendering a checkbox selection interface using inline keyboards in Aiogram.

    This widget allows users to select multiple options, toggle selections, and confirm or cancel their choices.

    Args:
        options (OptionsInput): A list of strings or a dictionary mapping keys to option metadata.
        can_select_none (bool, optional): Whether the user is allowed to proceed without selecting any option.
            Defaults to False.
        has_back_button (bool, optional): Whether to show a "Back" button in the interface.
            Defaults to False. If not explicitly set, it will automatically become True when `on_back` is provided.
        on_select (Optional[Callable[[CallbackQuery, dict], Awaitable[None]]], optional): Async callback invoked when
            the user presses "Done". Defaults to None.
        on_back (Optional[Callable[[CallbackQuery], Awaitable[None]]], optional): Async callback invoked when the user
            presses "Back". If set and `has_back_button` is not explicitly True, the button will still be shown.
    """

    _cb = CheckboxCB

    def __init__(
        self,
        options: OptionsInput,
        can_select_none: bool = False,
        has_back_button: bool = True,
        lang: LangCode = "en",
        on_select: Optional[Callable[[CallbackQuery, dict], Awaitable[None]]] = None,
        on_back: Optional[Callable[[CallbackQuery], Awaitable[None]]] = None,
    ):
        self._options: Dict[str, OptionMeta] = {}

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
        self._has_back_button = has_back_button or bool(on_back)
        self.on_select = on_select
        self.on_back = on_back
        self.lang = fallback_lang(lang)

        super().__init__()

    def is_selected_any(self) -> bool:
        """
        Checks whether any options are currently selected.

        Returns:
            bool: True if at least one option is selected, False otherwise.
        """
        for o in self._options.values():
            if o["flag"] is True:
                return True
        return False

    async def process_cb(
        self, c: CallbackQuery, data: CheckboxCB
    ) -> Optional[CheckboxResult]:
        """
        Processes the incoming callback query for this checkbox widget.

        Args:
            c (CallbackQuery): The callback query from the user.
            data (CheckboxCB): Parsed callback data.

        Returns:
            Optional[CheckboxResult]: A result object if in standalone mode, otherwise None.
        """
        if data.action == "IGNORE":
            await c.answer(cache_time=60)

        if data.action == "CHECK":
            self._options[data.arg]["flag"] = not self._options[data.arg]["flag"]
            await c.message.edit_reply_markup(reply_markup=await self.render_kb())

        elif data.action == "DONE":
            if not self._can_select_none and not self.is_selected_any():
                await c.answer(_TEXTS[self.lang]["at_least_one"])
                if not self.is_registered:
                    return CheckboxResult(False)
                return None

            if self.on_select:
                await self.on_select(c, self._options)
            elif self.is_registered:
                await c.message.edit_text(
                    json.dumps(self._options, indent=2, ensure_ascii=False)
                )
                await c.answer()
            else:
                return CheckboxResult(True, self._options)

        elif data.action == "BACK":
            if self.on_back:
                await self.on_back(c)
            elif self.is_registered:
                await c.message.delete()
                await c.answer("Ok")
            else:
                return CheckboxResult(True)

        if not self.is_registered:
            return CheckboxResult(False)
        return None

    async def render_kb(self):
        """
        Builds and returns the inline keyboard markup for the checkbox interface.

        Returns:
            InlineKeyboardMarkup: The rendered inline keyboard.
        """
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
        kb.row(
            ibtn(
                text=_TEXTS[self.lang]["done"],
                cb=self._cb(action="DONE", key=self._key),
            )
        )
        if self._has_back_button:
            kb.row(
                ibtn(
                    text=_TEXTS[self.lang]["back"],
                    cb=self._cb(action="BACK", key=self._key),
                )
            )
        return kb.as_markup()
