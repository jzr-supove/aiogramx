from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from typing import List, Optional, Protocol, runtime_checkable, Any

from aiogram.filters.callback_data import CallbackData
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


EMOJI_CONTROL_BUTTONS = ("🔼", "🔽", "⏫", "⏬")
ASCII_CONTROL_BUTTONS = ("^", "v", "^^", "vv")


@dataclass
class SelectionResult:
    completed: bool
    chosen_time: Optional[time] = None


class CBFields(Protocol):
    act: str
    hour: int = 0
    minute: int = 0


@runtime_checkable
class CallbackDataFactory(Protocol):
    def __call__(self, *, act: str, hour: int = 0, minute: int = 0) -> CallbackData: ...
    def filter(self) -> object: ...
    def pack(self) -> str: ...


def create_cb_class(prefix: str) -> CallbackDataFactory:
    class TsCB(CallbackData, prefix=f"aiogramx_ts_{prefix}"):
        act: str
        hour: int = 0
        minute: int = 0

    return TsCB  # type: ignore


class TimeSelectorBase(ABC):
    cb: CallbackDataFactory
    ignore_cb: str

    def __init_subclass__(cls, **kwargs: Any) -> None:
        if "prefix" not in kwargs:
            raise ValueError(
                f"prefix required, usage example: "
                f"`class {cls.__name__}(TimeSelectorBase, prefix='aiogramx_key'): ...`"
            )
        prefix = kwargs.pop("prefix")
        cls.cb = create_cb_class(prefix)
        cls.ignore_cb = cls.cb(act="IGNORE").pack()
        super().__init_subclass__(**kwargs)

    def __init__(
        self,
        allow_future_only: bool = False,
        past_time_warning: Optional[str] = None,
        delete_kb_on_select: bool = False,
        control_buttons: Optional[List[str]] = None,
    ):
        self.up1, self.down1, self.up2, self.down2 = (
            control_buttons or EMOJI_CONTROL_BUTTONS
        )
        self.allow_future_only = allow_future_only
        self.past_time_warning = past_time_warning or "Cannot select a past time"
        self.delete_kb_on_select = delete_kb_on_select

    def resolve_time(
        self,
        hour: Optional[int] = None,
        minute: Optional[int] = None,
        offset_minutes: int = 0,
    ) -> (int, int):
        base_dt = datetime.now()
        base_dt += timedelta(minutes=offset_minutes)

        final_hour = hour if hour is not None else base_dt.hour
        final_minute = minute if minute is not None else base_dt.minute

        t = time(hour=final_hour % 24, minute=final_minute % 60)
        return t.hour, t.minute

    @abstractmethod
    def render_kb(
        self,
        hour: Optional[int] = None,
        minute: Optional[int] = None,
        offset_minutes: int = 0,
    ) -> InlineKeyboardMarkup:
        pass

    @classmethod
    def filter(cls):
        return cls.cb.filter()

    async def handle_cb(
        self,
        query: CallbackQuery,
        data: CBFields,
        allow_future_only: Optional[bool] = None,
    ) -> SelectionResult:
        return_data = SelectionResult(completed=False, chosen_time=None)
        action, hour, minute = data.act, data.hour, data.minute

        if action == "IGNORE":
            await query.answer(cache_time=60)

        elif action == "CANCEL":
            return SelectionResult(completed=True, chosen_time=None)

        elif action == "DONE":
            now = datetime.now() + timedelta(minutes=1)
            selected = time(hour=hour, minute=minute)

            future_only = (
                allow_future_only
                if allow_future_only is not None
                else self.allow_future_only
            )
            if future_only and selected < now.time():
                await query.answer(self.past_time_warning, show_alert=True)
                return return_data

            if self.delete_kb_on_select:
                await query.message.delete_reply_markup()

            return_data = SelectionResult(
                completed=True, chosen_time=time(hour=hour, minute=minute)
            )

        elif action.startswith("INCR") or action.startswith("DECR"):
            if action == "INCR_H1":
                hour = (hour + 1) % 24

            elif action == "INCR_H10":
                hour = (hour + 10) % 24

            elif action == "INCR_M1":
                minute = (minute + 1) % 60

            elif action == "INCR_M10":
                minute = (minute + 10) % 60

            elif action == "DECR_H1":
                hour = (hour - 1) % 24

            elif action == "DECR_H10":
                hour = (hour - 10) % 24

            elif action == "DECR_M1":
                minute = (minute - 1) % 60

            elif action == "DECR_M10":
                minute = (minute - 10) % 60

            await query.message.edit_reply_markup(
                reply_markup=self.render_kb(hour, minute)
            )

        return return_data


class TimeSelectorGrid(TimeSelectorBase, prefix="grid"):
    def __init__(
        self,
        allow_future_only: bool = False,
        past_time_warning: Optional[str] = None,
        delete_kb_on_select: bool = False,
        control_buttons: Optional[List[str]] = None,
    ):
        super().__init__(
            allow_future_only, past_time_warning, delete_kb_on_select, control_buttons
        )

    def render_kb(
        self,
        hour: Optional[int] = None,
        minute: Optional[int] = None,
        offset_minutes: int = 0,
    ) -> InlineKeyboardMarkup:
        hour, minute = self.resolve_time(
            hour=hour, minute=minute, offset_minutes=offset_minutes
        )
        kb = InlineKeyboardBuilder()
        kb.row(
            InlineKeyboardButton(
                text=self.up2,
                callback_data=self.cb(act="INCR_H10", hour=hour, minute=minute).pack(),
            ),
            InlineKeyboardButton(
                text=self.up1,
                callback_data=self.cb(act="INCR_H1", hour=hour, minute=minute).pack(),
            ),
            InlineKeyboardButton(text=" ", callback_data=self.ignore_cb),
            InlineKeyboardButton(
                text=self.up2,
                callback_data=self.cb(act="INCR_M10", hour=hour, minute=minute).pack(),
            ),
            InlineKeyboardButton(
                text=self.up1,
                callback_data=self.cb(act="INCR_M1", hour=hour, minute=minute).pack(),
            ),
        )

        # MIDDLE ROW (TIME DISPLAY)
        kb.row(
            InlineKeyboardButton(
                text=str(hour).zfill(2)[0], callback_data=self.ignore_cb
            ),
            InlineKeyboardButton(
                text=str(hour).zfill(2)[1], callback_data=self.ignore_cb
            ),
            InlineKeyboardButton(text=" : ", callback_data=self.ignore_cb),
            InlineKeyboardButton(
                text=str(minute).zfill(2)[0], callback_data=self.ignore_cb
            ),
            InlineKeyboardButton(
                text=str(minute).zfill(2)[1], callback_data=self.ignore_cb
            ),
        )
        # ------------------------------

        kb.row(
            InlineKeyboardButton(
                text=self.down2,
                callback_data=self.cb(act="DECR_H10", hour=hour, minute=minute).pack(),
            ),
            InlineKeyboardButton(
                text=self.down1,
                callback_data=self.cb(act="DECR_H1", hour=hour, minute=minute).pack(),
            ),
            InlineKeyboardButton(text=" ", callback_data=self.ignore_cb),
            InlineKeyboardButton(
                text=self.down2,
                callback_data=self.cb(act="DECR_M10", hour=hour, minute=minute).pack(),
            ),
            InlineKeyboardButton(
                text=self.down1,
                callback_data=self.cb(act="DECR_M1", hour=hour, minute=minute).pack(),
            ),
        )
        kb.row(
            InlineKeyboardButton(
                text="🔙",
                callback_data=self.cb(act="CANCEL", hour=hour, minute=minute).pack(),
            ),
            InlineKeyboardButton(
                text="☑️",
                callback_data=self.cb(act="DONE", hour=hour, minute=minute).pack(),
            ),
        )
        return kb.as_markup()


class TimeSelectorModern(TimeSelectorBase, prefix="modern"):
    def __init__(
        self,
        allow_future_only: bool = False,
        past_time_warning: Optional[str] = None,
        delete_kb_on_select: bool = False,
        control_buttons: Optional[List[str]] = None,
    ):
        super().__init__(
            allow_future_only, past_time_warning, delete_kb_on_select, control_buttons
        )

    def render_kb(
        self,
        hour: Optional[int] = None,
        minute: Optional[int] = None,
        offset_minutes: int = 0,
    ) -> InlineKeyboardMarkup:
        hour, minute = self.resolve_time(
            hour=hour, minute=minute, offset_minutes=offset_minutes
        )
        kb = InlineKeyboardBuilder()

        # UP CONTROLLERS
        kb.row(
            InlineKeyboardButton(
                text=self.up2,
                callback_data=self.cb(act="INCR_H10", hour=hour, minute=minute).pack(),
            ),
            InlineKeyboardButton(
                text=self.up1,
                callback_data=self.cb(act="INCR_H1", hour=hour, minute=minute).pack(),
            ),
            InlineKeyboardButton(
                text=self.up2,
                callback_data=self.cb(act="INCR_M10", hour=hour, minute=minute).pack(),
            ),
            InlineKeyboardButton(
                text=self.up1,
                callback_data=self.cb(act="INCR_M1", hour=hour, minute=minute).pack(),
            ),
        )

        # TIME DISPLAY
        space = " " * 10
        kb.row(
            InlineKeyboardButton(
                text=f"{space}{hour:02}{space}:{space}{minute:02}{space}",
                callback_data=self.ignore_cb,
            ),
        )

        # DOWN CONTROLLERS
        kb.row(
            InlineKeyboardButton(
                text=self.down2,
                callback_data=self.cb(act="DECR_H10", hour=hour, minute=minute).pack(),
            ),
            InlineKeyboardButton(
                text=self.down1,
                callback_data=self.cb(act="DECR_H1", hour=hour, minute=minute).pack(),
            ),
            InlineKeyboardButton(
                text=self.down2,
                callback_data=self.cb(act="DECR_M10", hour=hour, minute=minute).pack(),
            ),
            InlineKeyboardButton(
                text=self.down1,
                callback_data=self.cb(act="DECR_M1", hour=hour, minute=minute).pack(),
            ),
        )

        # STATE CONTROLLERS
        kb.row(
            InlineKeyboardButton(
                text="🔙",
                callback_data=self.cb(act="CANCEL", hour=hour, minute=minute).pack(),
            ),
            InlineKeyboardButton(
                text="☑️",
                callback_data=self.cb(act="DONE", hour=hour, minute=minute).pack(),
            ),
        )

        return kb.as_markup()
