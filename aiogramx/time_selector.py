from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from typing import List, Optional, Callable, Awaitable, Tuple

from aiogram import Router
from aiogram.filters.callback_data import CallbackData
from aiogram.types import CallbackQuery, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from aiogramx.base import WidgetBase
from aiogramx.utils import ibtn, fallback_lang


EMOJI_CONTROL_BUTTONS = ("🔼", "🔽", "⏫", "⏬")
ASCII_CONTROL_BUTTONS = ("^", "v", "^^", "vv")

_TEXTS = {
    "en": {"PAST_TIME_WARN": "⚠️ Cannot select a past time"},
    "ru": {"PAST_TIME_WARN": "⚠️ Невозможно выбрать прошедшее время"},
    "uz": {"PAST_TIME_WARN": "⚠️ O‘tgan vaqtni tanlab bo‘lmaydi"},
}


@dataclass
class SelectionResult:
    """Represents the result of a time selection process.

    Attributes:
        completed (bool): Whether the time selection was completed.
        chosen_time (Optional[time]): The selected time, if any.
    """

    completed: bool
    chosen_time: Optional[time] = None


class TimeSelectorCB(CallbackData, prefix="aiogramx_ts"):
    """Callback data structure for time selector interactions.

    Attributes:
        act (str): Action to perform (e.g., increment, decrement, done).
        hour (int): Selected hour.
        minute (int): Selected minute.
        key (str): Key for widget instance identification.
    """

    act: str
    hour: int = 0
    minute: int = 0
    key: str = ""


class TimeSelectorBase(ABC, WidgetBase[TimeSelectorCB, "TimeSelectorBase"]):
    """Abstract base class for building time selection widgets in AiogramX.

    Provides common logic and validation for selecting times through inline buttons.
    Supports constraints like allowing only future times, automatic hour overflow handling,
    and custom button configuration.

    Args:
        allow_future_only (bool): If True, restricts selection to future times. (fefault: False)
        carry_over (bool): If True, minute overflows/underflows automatically adjust the hour.
        on_select (Optional[Callable[[CallbackQuery, time], Awaitable[None]]]):
            Async callback to be triggered when a valid time is selected.
        on_back (Optional[Callable[[CallbackQuery], Awaitable[None]]]):
            Async callback to be triggered when the back button is pressed.
        lang (str): Language code used for UI text (defaults to "en").
        past_time_warn_text (Optional[str]): Custom warning text shown when a past time is selected when `allow_future_only` is set to True.
        control_buttons (Optional[List[str]]): Custom symbols for the 4 directional buttons
            in the order: up1, down1, up2, down2.
        done_button_text (Optional[str]): Custom label for the "Done" button.
        back_button_text (Optional[str]): Custom label for the "Back" button.

    Raises:
        TypeError: If `control_buttons` is not a list/tuple of 4 strings.
        ValueError: If `control_buttons` does not contain exactly 4 elements.
    """

    _cb = TimeSelectorCB
    _registered = False

    def __init__(
        self,
        allow_future_only: bool = False,
        carry_over: bool = False,
        on_select: Optional[Callable[[CallbackQuery, time], Awaitable[None]]] = None,
        on_back: Optional[Callable[[CallbackQuery], Awaitable[None]]] = None,
        lang: Optional[str] = "en",
        past_time_warn_text: Optional[str] = None,
        control_buttons: Optional[List[str]] = None,
        done_button_text: Optional[str] = None,
        back_button_text: Optional[str] = None,
    ):
        if control_buttons is not None:
            if not isinstance(control_buttons, (list, tuple)):
                raise TypeError("control_buttons must be a list or tuple of 4 strings.")
            if len(control_buttons) != 4:
                raise ValueError("control_buttons must contain exactly 4 elements.")
            if not all(isinstance(btn, str) for btn in control_buttons):
                raise TypeError("All elements in control_buttons must be strings.")

        self.up1, self.down1, self.up2, self.down2 = (
            control_buttons or EMOJI_CONTROL_BUTTONS
        )
        self.allow_future_only = allow_future_only
        self.carry_over = carry_over
        self.on_select = on_select
        self.on_back = on_back
        self.lang = fallback_lang(lang)
        self._past_time_warn_text = (
            past_time_warn_text or _TEXTS[self.lang]["PAST_TIME_WARN"]
        )
        self._done_button_text = done_button_text or "☑️"
        self._back_button_text = back_button_text or "🔙"

        super().__init__()

    def __init_subclass__(cls, **kwargs):
        """
        Ensures all subclasses of TimeSelectorBase share the same storage and registration state.

        This overrides the default WidgetBase behavior, which would assign each subclass its own
        `_storage` and `_registered` attributes. By explicitly setting these attributes to reference
        those of TimeSelectorBase, this method enforces a shared widget registry across all
        concrete implementations like TimeSelectorGrid and TimeSelectorModern.

        Args:
            **kwargs: Additional keyword arguments passed to the superclass initializer.
        """
        super().__init_subclass__(**kwargs)
        cls._storage = TimeSelectorBase._storage
        cls._registered = TimeSelectorBase._registered

    @classmethod
    def register(cls, router: Router) -> None:
        """
        Registers the shared widget class with the Aiogram router, if not already registered.

        Prevents multiple registrations across subclasses by ensuring only a single registration
        occurs for all TimeSelectorBase-derived classes. This allows different visual variants
        (e.g., grid or modern layout) to interoperate using the same callback handling logic.

        Args:
            router (Router): The router instance to register this widget's callback handler with.
        """
        if TimeSelectorBase._registered:
            return
        super().register(router)
        TimeSelectorBase._registered = True

    @property
    def is_registered(self) -> bool:
        """
        Indicates whether the time selector widget has been registered with the router.

        This reflects the shared registration status across all TimeSelectorBase-based
        widget implementations. Useful for conditional behavior depending on whether
        the widget system is operating in registered (router-connected) mode.

        Returns:
            bool: True if registered, False otherwise.
        """
        return TimeSelectorBase._registered

    def _(self, act: str, hour: int = 0, minute: int = 0) -> str:
        """Packs callback data into a string with key implicitly.

        Args:
            act (str): Action identifier.
            hour (int): Selected hour.
            minute (int): Selected minute.

        Returns:
            str: Packed callback data string.
        """
        return self._cb(act=act, hour=hour, minute=minute, key=self._key).pack()

    def _resolve_time(
        self,
        hour: Optional[int] = None,
        minute: Optional[int] = None,
        offset_minutes: int = 0,
    ) -> (int, int):
        """Resolves a time from given inputs or current time with offset.

        Args:
            hour (Optional[int]): Hour to resolve. Defaults to current hour.
            minute (Optional[int]): Minute to resolve. Defaults to current minute.
            offset_minutes (int): Offset in minutes to apply to current time.

        Returns:
            Tuple[int, int]: Resolved hour and minute.
        """
        base_dt = datetime.now()
        base_dt += timedelta(minutes=offset_minutes)

        final_hour = hour if hour is not None else base_dt.hour
        final_minute = minute if minute is not None else base_dt.minute

        t = time(hour=final_hour % 24, minute=final_minute % 60)
        return t.hour, t.minute

    def _adjust_minute(
        self, hour: int, minute: int, delta_minute: int
    ) -> Tuple[int, int]:
        """Adjusts the minute value with optional carry-over to the hour.

        Increments or decrements the minute by a given delta. If `carry_over` is enabled
        and the resulting minute value overflows (>= 60) or underflows (< 0), the hour
        is adjusted accordingly. The final minute is wrapped to stay within 0–59.

        Args:
            hour (int): The current hour (0–23).
            minute (int): The current minute (0–59).
            delta_minute (int): The number of minutes to adjust (positive or negative).

        Returns:
            Tuple[int, int]: A tuple of (hour, minute) after adjustment.
        """

        minute += delta_minute

        if self.carry_over:
            if minute > 59:
                hour = (hour + 1) % 24
            elif minute < 0:
                hour = (hour - 1) % 24

        minute %= 60
        return hour, minute

    def _attach_control_buttons(
        self, builder: InlineKeyboardBuilder, hour: int, minute: int
    ) -> None:
        """Attach 'Back' and 'Done' control buttons to the keyboard builder.

        Adds the back and done buttons to the provided `InlineKeyboardBuilder` instance.
        Button placement adapts based on the length of their text to ensure a clean layout.

        Args:
            builder (InlineKeyboardBuilder): The keyboard builder to which the buttons are added.
            hour (int): The hour value used for callback data formatting.
            minute (int): The minute value used for callback data formatting.

        Returns:
            None
        """
        back_btn = ibtn(text=self._back_button_text, cb=self._("CANCEL", hour, minute))
        done_btn = ibtn(text=self._done_button_text, cb=self._("DONE", hour, minute))

        # Smart alignment of control buttons based on text length
        if len(self._back_button_text) <= 15 and len(self._done_button_text) <= 15:
            builder.row(back_btn, done_btn)
        else:
            builder.row(done_btn)
            builder.row(back_btn)

    async def process_cb(
        self,
        query: CallbackQuery,
        data: TimeSelectorCB,
        allow_future_only: Optional[bool] = None,
    ) -> Optional[SelectionResult]:
        """Processes a callback query and updates UI or state accordingly.

        Args:
            query (CallbackQuery): The incoming callback query.
            data (TimeSelectorCB): Parsed callback data.
            allow_future_only (Optional[bool]): Optional override for future-only constraint.

        Returns:
            Optional[SelectionResult]: Result of processing the callback, if any.
        """
        return_data = SelectionResult(completed=False, chosen_time=None)
        action, hour, minute = data.act, data.hour, data.minute

        if action == "IGNORE":
            await query.answer(cache_time=60)

        elif action == "CANCEL":
            if self.on_back:
                await self.on_back(query)
            elif self.is_registered:
                await query.message.edit_text("Operation canceled")
                await query.answer()
            else:
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
                await query.answer(self._past_time_warn_text, show_alert=True)

                if not self.is_registered:
                    return return_data
                return None

            if self.on_select:
                await self.on_select(query, selected)
            elif self.is_registered:
                await query.message.edit_text(
                    f"Selected time: {selected.strftime('%H:%M')}"
                )
                await query.answer()
            else:
                return SelectionResult(completed=True, chosen_time=selected)

        elif action.startswith("INCR") or action.startswith("DECR"):
            if action == "INCR_H1":
                hour = (hour + 1) % 24

            elif action == "INCR_H10":
                hour = (hour + 10) % 24

            elif action == "INCR_M1":
                hour, minute = self._adjust_minute(hour, minute, delta_minute=1)

            elif action == "INCR_M10":
                hour, minute = self._adjust_minute(hour, minute, delta_minute=10)

            elif action == "DECR_H1":
                hour = (hour - 1) % 24

            elif action == "DECR_H10":
                hour = (hour - 10) % 24

            elif action == "DECR_M1":
                hour, minute = self._adjust_minute(hour, minute, delta_minute=-1)

            elif action == "DECR_M10":
                hour, minute = self._adjust_minute(hour, minute, delta_minute=-10)

            await query.message.edit_reply_markup(
                reply_markup=self.render_kb(hour, minute)
            )

        if not self.is_registered:
            return return_data
        return None

    @abstractmethod
    def render_kb(
        self,
        hour: Optional[int] = None,
        minute: Optional[int] = None,
        offset_minutes: int = 0,
    ) -> InlineKeyboardMarkup:
        """Render the inline keyboard markup for time selection.

        Args:
            hour (Optional[int]): Current hour.
            minute (Optional[int]): Current minute.
            offset_minutes (int): Offset to apply to current time.

        Returns:
            InlineKeyboardMarkup: Inline keyboard for time input.
        """
        pass


class TimeSelectorGrid(TimeSelectorBase):
    """Concrete implementation of TimeSelectorBase using a grid layout.

    Args:
        allow_future_only (bool): If True, restricts selection to future times. (fefault: False)
        carry_over (bool): If True, minute overflows/underflows automatically adjust the hour.
        on_select (Optional[Callable[[CallbackQuery, time], Awaitable[None]]]):
            Async callback to be triggered when a valid time is selected.
        on_back (Optional[Callable[[CallbackQuery], Awaitable[None]]]):
            Async callback to be triggered when the back button is pressed.
        lang (str): Language code used for UI text (defaults to "en").
        past_time_warn_text (Optional[str]): Custom warning text shown when a past time is selected when `allow_future_only` is set to True.
        control_buttons (Optional[List[str]]): Custom symbols for the 4 directional buttons
            in the order: up1, down1, up2, down2.
        done_button_text (Optional[str]): Custom label for the "Done" button.
        back_button_text (Optional[str]): Custom label for the "Back" button.

    Raises:
        TypeError: If `control_buttons` is not a list/tuple of 4 strings.
        ValueError: If `control_buttons` does not contain exactly 4 elements.
    """

    def __init__(
        self,
        allow_future_only: bool = False,
        carry_over: bool = False,
        on_select: Optional[Callable[[CallbackQuery, time], Awaitable[None]]] = None,
        on_back: Optional[Callable[[CallbackQuery], Awaitable[None]]] = None,
        lang: Optional[str] = "en",
        past_time_warn_text: Optional[str] = None,
        control_buttons: Optional[List[str]] = None,
        done_button_text: Optional[str] = None,
        back_button_text: Optional[str] = None,
    ):
        super().__init__(
            allow_future_only,
            carry_over,
            on_select,
            on_back,
            lang,
            past_time_warn_text,
            control_buttons,
            done_button_text,
            back_button_text,
        )

    def render_kb(
        self,
        hour: Optional[int] = None,
        minute: Optional[int] = None,
        offset_minutes: int = 0,
    ) -> InlineKeyboardMarkup:
        """
        Renders the keyboard in a grid layout for selecting time.

        Args:
            hour (Optional[int]): Hour to display.
            minute (Optional[int]): Minute to display.
            offset_minutes (int): Offset in minutes to apply to base time.

        Returns:
            InlineKeyboardMarkup: Inline keyboard with time controls.
        """
        hour, minute = self._resolve_time(hour, minute, offset_minutes)
        ignore_cb = self._(act="IGNORE")
        kb = InlineKeyboardBuilder()

        # UP CONTROLLERS
        kb.row(
            ibtn(text=self.up2, cb=self._("INCR_H10", hour, minute)),
            ibtn(text=self.up1, cb=self._("INCR_H1", hour, minute)),
            ibtn(text=" ", cb=ignore_cb),
            ibtn(text=self.up2, cb=self._("INCR_M10", hour, minute)),
            ibtn(text=self.up1, cb=self._("INCR_M1", hour, minute)),
        )

        # TIME DISPLAY BUTTONS
        kb.row(
            ibtn(text=str(hour).zfill(2)[0], cb=ignore_cb),
            ibtn(text=str(hour).zfill(2)[1], cb=ignore_cb),
            ibtn(text=" : ", cb=ignore_cb),
            ibtn(text=str(minute).zfill(2)[0], cb=ignore_cb),
            ibtn(text=str(minute).zfill(2)[1], cb=ignore_cb),
        )

        # DOWN CONTROLLERS
        kb.row(
            ibtn(text=self.down2, cb=self._("DECR_H10", hour, minute)),
            ibtn(text=self.down1, cb=self._("DECR_H1", hour, minute)),
            ibtn(text=" ", cb=ignore_cb),
            ibtn(text=self.down2, cb=self._("DECR_M10", hour, minute)),
            ibtn(text=self.down1, cb=self._("DECR_M1", hour, minute)),
        )

        # CONTROL BUTTONS
        self._attach_control_buttons(kb, hour, minute)

        return kb.as_markup()


class TimeSelectorModern(TimeSelectorBase):
    """Modern visual implementation of time selector with linear layout.

    Args:
        allow_future_only (bool): If True, restricts selection to future times. (fefault: False)
        carry_over (bool): If True, minute overflows/underflows automatically adjust the hour.
        on_select (Optional[Callable[[CallbackQuery, time], Awaitable[None]]]):
            Async callback to be triggered when a valid time is selected.
        on_back (Optional[Callable[[CallbackQuery], Awaitable[None]]]):
            Async callback to be triggered when the back button is pressed.
        lang (str): Language code used for UI text (defaults to "en").
        past_time_warn_text (Optional[str]): Custom warning text shown when a past time is selected when `allow_future_only` is set to True.
        control_buttons (Optional[List[str]]): Custom symbols for the 4 directional buttons
            in the order: up1, down1, up2, down2.
        done_button_text (Optional[str]): Custom label for the "Done" button.
        back_button_text (Optional[str]): Custom label for the "Back" button.

    Raises:
        TypeError: If `control_buttons` is not a list/tuple of 4 strings.
        ValueError: If `control_buttons` does not contain exactly 4 elements.
    """

    def __init__(
        self,
        allow_future_only: bool = False,
        carry_over: bool = False,
        on_select: Optional[Callable[[CallbackQuery, time], Awaitable[None]]] = None,
        on_back: Optional[Callable[[CallbackQuery], Awaitable[None]]] = None,
        lang: Optional[str] = "en",
        past_time_warn_text: Optional[str] = None,
        control_buttons: Optional[List[str]] = None,
        done_button_text: Optional[str] = None,
        back_button_text: Optional[str] = None,
    ):
        super().__init__(
            allow_future_only,
            carry_over,
            on_select,
            on_back,
            lang,
            past_time_warn_text,
            control_buttons,
            done_button_text,
            back_button_text,
        )

    def render_kb(
        self,
        hour: Optional[int] = None,
        minute: Optional[int] = None,
        offset_minutes: int = 0,
    ) -> InlineKeyboardMarkup:
        """
        Renders the keyboard in a modern, centered layout.

        Args:
            hour (Optional[int]): Hour to display.
            minute (Optional[int]): Minute to display.
            offset_minutes (int): Offset in minutes to apply to base time.

        Returns:
            InlineKeyboardMarkup: Inline keyboard with time controls.
        """
        hour, minute = self._resolve_time(hour, minute, offset_minutes)
        kb = InlineKeyboardBuilder()
        ignore_cb = self._(act="IGNORE")

        # UP CONTROLLERS
        kb.row(
            ibtn(text=self.up2, cb=self._("INCR_H10", hour, minute)),
            ibtn(text=self.up1, cb=self._("INCR_H1", hour, minute)),
            ibtn(text=self.up2, cb=self._("INCR_M10", hour, minute)),
            ibtn(text=self.up1, cb=self._("INCR_M1", hour, minute)),
        )

        # TIME DISPLAY
        _ = " " * 10
        time_str = f"{_}{hour:02}{_}:{_}{minute:02}{_}"
        kb.row(ibtn(text=time_str, cb=ignore_cb))

        # DOWN CONTROLLERS
        kb.row(
            ibtn(text=self.down2, cb=self._("DECR_H10", hour, minute)),
            ibtn(text=self.down1, cb=self._("DECR_H1", hour, minute)),
            ibtn(text=self.down2, cb=self._("DECR_M10", hour, minute)),
            ibtn(text=self.down1, cb=self._("DECR_M1", hour, minute)),
        )

        # CONTROL BUTTONS
        self._attach_control_buttons(kb, hour, minute)

        return kb.as_markup()
