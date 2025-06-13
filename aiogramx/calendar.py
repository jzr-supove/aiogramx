import calendar
from dataclasses import dataclass
from datetime import timedelta, date
from typing import Optional, Union, Callable, Awaitable

from aiogram.filters.callback_data import CallbackData
from aiogram.types import CallbackQuery
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from aiogramx.base import WidgetBase
from aiogramx.utils import ibtn, fallback_lang


_TEXTS = {
    "en": {
        "TODAY": "Today",
        "TOMORROW": "Tomorrow",
        "OVERMORROW": "Overmorrow",
        "WEEKS": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        "WARN_PAST": "⚠️ Can't select past",
        "WARN_FUTURE": "⚠️ Can't select far future",
        "BACK": "🔙 Back",
        "EXPIRED": "⚠️ Calendar keyboard is expired",
    },
    "ru": {
        "TODAY": "Сегодня",
        "TOMORROW": "Завтра",
        "OVERMORROW": "Послезавтра",
        "WEEKS": ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"],
        "WARN_PAST": "⚠️ Нельзя выбрать прошедшую дату",
        "WARN_FUTURE": "⚠️ Нельзя выбрать далёкое будущее",
        "BACK": "🔙 Назад",
        "EXPIRED": "⚠️ Срок действия календарной клавиатуры истек",
    },
    "uz": {
        "TODAY": "Bugun",
        "TOMORROW": "Ertaga",
        "OVERMORROW": "Indinga",
        "WEEKS": ["Du", "Se", "Ch", "Pa", "Ju", "Sh", "Ya"],
        "WARN_PAST": "⚠️ O‘tgan sanani tanlab bo‘lmaydi",
        "WARN_FUTURE": "⚠️ Juda uzoq kelajak sanani tanlab bo‘lmaydi",
        "BACK": "🔙 Orqaga",
        "EXPIRED": "⚠️ Kalendar klaviaturasi muddati tugagan",
    },
}


@dataclass
class CalendarResult:
    """
    Represents the result of an interaction with the Calendar widget.

    Attributes:
        completed (bool): Indicates whether the user completed the calendar interaction
            (e.g., selected a date or pressed "Back").
        chosen_date (Optional[date]): The selected date, if any. None if the interaction
            was canceled or not completed.
    """

    completed: bool
    chosen_date: Optional[date] = None


class CalendarCB(CallbackData, prefix="aiogramx_calendar"):
    """
    Represents structured callback data for the Calendar widget.

    Attributes:
        action (str): The action associated with the callback, such as "DAY",
            "NEXT-MONTH", "PREV-YEAR", etc.
        year (int): The year related to the calendar action (e.g., selected or navigated year).
        month (int): The month related to the calendar action.
        day (int): The day related to the calendar action.
        key (str): A unique identifier key for this calendar instance, used to ensure
            callbacks belong to the correct widget context.
    """

    action: str
    year: int = 0
    month: int = 0
    day: int = 0
    key: str = ""


class Calendar(WidgetBase[CalendarCB, "Calendar"]):
    """
    An inline calendar widget for date selection in Telegram bots using AiogramX.

    This widget allows users to navigate through months and years, and select dates.
    It supports features like restricting date range, disabling past dates, and
    displaying quick buttons for selecting today, tomorrow, or the day after tomorrow.

    Args:
        max_range (timedelta): The maximum allowed future range from today.
        can_select_past (bool): Whether users are allowed to select past dates.
        show_quick_buttons (bool): Whether to show quick selection buttons for
            "Today", "Tomorrow", and "Overmorrow".
        on_select (Optional[Callable[[CallbackQuery, date], Awaitable[None]]]):
            Callback function called when a date is selected.
        on_back (Optional[Callable[[CallbackQuery], Awaitable[None]]]):
            Callback function called when the back button is pressed.
        lang (str): Language code for localization.
        warn_past_text (Optional[str]): Text shown when a past date is selected and not allowed.
        warn_future_text (Optional[str]): Text shown when a date outside the allowed future
            range is selected.
        back_button_text (Optional[str]): Custom label for the "Back" button.

    Methods:
        render_kb(year: Optional[int] = None, month: Optional[int] = None)
            -> InlineKeyboardMarkup:
            Renders the calendar as an inline keyboard for the specified month and year.

        process_cb(c: CallbackQuery, data: CalendarCB) -> Optional[CalendarResult]:
            Handles the callback data for the calendar, such as navigation and date selection.

    Usage Example:
        calendar = Calendar(max_range=timedelta(days=30), show_quick_buttons=True)
        await message.answer("Choose a date:", reply_markup=await calendar.render_kb())
    """

    _cb = CalendarCB

    def __init__(
        self,
        max_range: Optional[timedelta] = None,
        can_select_past: bool = True,
        show_quick_buttons: bool = False,
        on_select: Optional[Callable[[CallbackQuery, date], Awaitable[None]]] = None,
        on_back: Optional[Callable[[CallbackQuery], Awaitable[None]]] = None,
        lang: Optional[str] = "en",
        warn_past_text: Optional[str] = None,
        warn_future_text: Optional[str] = None,
        back_button_text: Optional[str] = None,
    ):
        self.max_range = max_range
        self._can_select_past = can_select_past
        self._show_quick_buttons = show_quick_buttons
        self.on_select = on_select
        self.on_back = on_back

        self.lang = fallback_lang(lang)
        self._warn_past_text = warn_past_text or self._t("WARN_PAST")
        self._warn_future_text = warn_future_text or self._t("WARN_FUTURE")
        self._back_button_text = back_button_text or self._t("BACK")

        super().__init__()

    def _t(self, text_id: str) -> Union[str, list[str]]:
        """
        Retrieve a localized string or list of strings by ID.

        Args:
            text_id (str): The identifier of the text to retrieve.

        Returns:
            Union[str, list[str]]: The localized string or list of strings.
        """
        return _TEXTS[self.lang][text_id.upper()]

    @classmethod
    def get_expired_text(cls, lang: str = "en") -> str:
        """
        Returns the expiration notice text for an expired calendar keyboard.

        Args:
            lang (str): Language code (default is "en").

        Returns:
            str: The expired keyboard message in the selected language.
        """

        return _TEXTS[lang]["EXPIRED"]

    def render_kb(
        self, year: Optional[int] = None, month: Optional[int] = None
    ) -> InlineKeyboardMarkup:
        """
        Builds and returns an inline keyboard representing a calendar.

        Args:
            year (Optional[int]): The year to display. Defaults to the current year if None.
            month (Optional[int]): The month to display. Defaults to the current month if None.

        Returns:
            InlineKeyboardMarkup: The constructed inline keyboard for the specified month and year.
        """
        today = date.today()
        year = today.year if year is None else year
        month = today.month if month is None else month

        kb = InlineKeyboardBuilder()
        ignore_cb = self._cb(action="IGNORE", key=self._key).pack()
        empty_btn = ibtn(text="  ", cb=ignore_cb)
        prev_year_btn = next_year_btn = prev_month_btn = next_month_btn = empty_btn

        # Quick Buttons
        if self._show_quick_buttons:
            tomorrow = today + timedelta(days=1)
            overmorrow = today + timedelta(days=2)
            kb.row(
                ibtn(
                    text=self._t("TODAY"),
                    cb=self._cb(
                        action="DAY",
                        year=today.year,
                        month=today.month,
                        day=today.day,
                        key=self._key,
                    ),
                ),
                ibtn(
                    text=self._t("TOMORROW"),
                    cb=self._cb(
                        action="DAY",
                        year=tomorrow.year,
                        month=tomorrow.month,
                        day=tomorrow.day,
                        key=self._key,
                    ),
                ),
                ibtn(
                    text=self._t("OVERMORROW"),
                    cb=self._cb(
                        action="DAY",
                        year=overmorrow.year,
                        month=overmorrow.month,
                        day=overmorrow.day,
                        key=self._key,
                    ),
                ),
            )

        # Month Control Buttons
        if self._can_select_past or month - 1 >= today.month:
            prev_month_btn = ibtn(
                text="<",
                cb=self._cb(
                    action="PREV-MONTH",
                    year=year,
                    month=month,
                    key=self._key,
                ),
            )

        if month == 12:
            next_month = date(year + 1, 1, 1)
        else:
            next_month = date(year, month + 1, 1)

        if not self.max_range or next_month - today < self.max_range:
            next_month_btn = ibtn(
                text=">",
                cb=self._cb(
                    action="NEXT-MONTH",
                    year=year,
                    month=month,
                    key=self._key,
                ),
            )

        # Year Control Buttons
        if self._can_select_past or year - 1 >= today.year:
            prev_year_btn = ibtn(
                "<<",
                self._cb(
                    action="PREV-YEAR",
                    year=year,
                    month=month,
                    key=self._key,
                ),
            )

        if (
            not self.max_range
            or date(year=year + 1, month=month, day=1) - today < self.max_range
        ):
            next_year_btn = ibtn(
                ">>",
                self._cb(
                    action="NEXT-YEAR",
                    year=year,
                    month=month,
                    key=self._key,
                ),
            )

        # Days of month
        days_kb = InlineKeyboardBuilder()

        for week in calendar.monthcalendar(year, month):
            for day in week:
                if day == 0:
                    days_kb.add(empty_btn)
                    continue

                dt = date(year=year, month=month, day=day)

                if dt < today and not self._can_select_past:
                    cb = self._cb(action="WARN_PAST", key=self._key).pack()
                elif self.max_range and dt > today and dt - today > self.max_range:
                    cb = self._cb(action="WARN_FUTURE", key=self._key).pack()
                else:
                    cb = self._cb(
                        action="DAY", year=year, month=month, day=day, key=self._key
                    ).pack()

                is_today = (
                    day == today.day and month == today.month and year == today.year
                )
                days_kb.add(ibtn(text=f"• {day} •" if is_today else str(day), cb=cb))

        days_kb.adjust(7)

        # Build Keyboard
        # Month Controls
        kb.row(
            prev_month_btn,
            ibtn(f"{calendar.month_name[month]} {str(year)}", cb=ignore_cb),
            next_month_btn,
        )

        # Week Day Names
        kb.row(*[ibtn(day_name, cb=ignore_cb) for day_name in self._t("WEEKS")])

        # Days of month
        kb.attach(days_kb)

        # Year Controls
        kb.row(prev_year_btn, empty_btn, next_year_btn)

        # Back Navigator
        kb.row(ibtn(self._back_button_text, self._cb(action="BACK", key=self._key)))
        return kb.as_markup()

    async def process_cb(
        self, c: CallbackQuery, data: CalendarCB
    ) -> Optional[CalendarResult]:
        """
        Processes user interaction with the calendar widget via callback data.

        Handles navigation (month/year changes), date selections, and quick buttons.
        Optionally invokes `on_select` or `on_back` callbacks.

        Args:
            c (CallbackQuery): The incoming callback query from the user.
            data (CalendarCB): Parsed callback data associated with the calendar.

        Returns:
            Optional[CalendarResult]: If the widget is not registered globally, returns a
            CalendarResult indicating if a date was selected and the selected date. Returns
            None if handled via a registered handler.
        """
        result = CalendarResult(completed=False, chosen_date=None)

        if data.action == "IGNORE":
            await c.answer(cache_time=60)

        elif data.action == "WARN_PAST":
            await c.answer(self._warn_past_text, show_alert=True)

        elif data.action == "WARN_FUTURE":
            await c.answer(self._warn_future_text, show_alert=True)

        elif data.action == "BACK":
            if self.on_back:
                await self.on_back(c)
            elif self.is_registered:
                await c.message.edit_text(text="Ok")
                await c.answer()
            else:
                result = CalendarResult(completed=True, chosen_date=None)

        # user selects a date, process the date
        elif data.action == "DAY":
            dt = date(data.year, data.month, data.day)

            if self.on_select:
                await self.on_select(c, dt)
            elif self.is_registered:
                await c.message.edit_text(
                    text=f"{data.year}-{data.month:02d}-{data.day:02d}"
                )
                await c.answer()
            else:
                result = CalendarResult(completed=True, chosen_date=dt)

        # user navigates to previous year, editing message with new calendar
        elif data.action == "PREV-YEAR":
            prev_date = date(data.year, data.month, 1) - timedelta(days=365)
            await c.message.edit_reply_markup(
                reply_markup=self.render_kb(prev_date.year, prev_date.month)
            )
            await c.answer()

        # user navigates to next year, editing message with new calendar
        elif data.action == "NEXT-YEAR":
            next_date = date(data.year, data.month, 1) + timedelta(days=365)
            await c.message.edit_reply_markup(
                reply_markup=self.render_kb(next_date.year, next_date.month)
            )
            await c.answer()

        # user navigates to previous month, editing message with new calendar
        elif data.action == "PREV-MONTH":
            prev_date = date(data.year, data.month, 1) - timedelta(days=1)
            await c.message.edit_reply_markup(
                reply_markup=self.render_kb(prev_date.year, prev_date.month)
            )
            await c.answer()

        # user navigates to next month, editing message with new calendar
        elif data.action == "NEXT-MONTH":
            next_date = date(data.year, data.month, 1) + timedelta(days=31)
            await c.message.edit_reply_markup(
                reply_markup=self.render_kb(next_date.year, next_date.month)
            )
            await c.answer()

        if not self.is_registered:
            return result
        return None
