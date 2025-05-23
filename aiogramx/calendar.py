import calendar
from dataclasses import dataclass
from datetime import timedelta, date
from typing import Optional, Literal, Union, Callable, Awaitable

from aiogram import Router
from aiogram.filters.callback_data import CallbackData
from aiogram.types import CallbackQuery
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from flipcache import LRUDict

from aiogramx.utils import ibtn, gen_key, silent_fail

LangCode = Literal["EN", "RU", "UZ"]


__TEXTS__ = {
    "EN": {
        "TODAY": "Today",
        "TOMORROW": "Tomorrow",
        "OVERMORROW": "Overmorrow",
        "WEEKS": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        "WARN_PAST": "Can't select past",
        "WARN_FUTURE": "Can't select far future",
        "BACK": "🔙 Back",
        "EXPIRED": "Calendar keyboard is expired",
    },
    "RU": {
        "TODAY": "Сегодня",
        "TOMORROW": "Завтра",
        "OVERMORROW": "Послезавтра",
        "WEEKS": ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"],
        "WARN_PAST": "Нельзя выбрать прошедшую дату",
        "WARN_FUTURE": "Нельзя выбрать далёкое будущее",
        "BACK": "🔙 Назад",
        "EXPIRED": "Срок действия календарной клавиатуры истек",
    },
    "UZ": {
        "TODAY": "Bugun",
        "TOMORROW": "Ertaga",
        "OVERMORROW": "Indinga",
        "WEEKS": ["Du", "Se", "Ch", "Pa", "Ju", "Sh", "Ya"],
        "WARN_PAST": "O‘tgan sanani tanlab bo‘lmaydi",
        "WARN_FUTURE": "Juda uzoq kelajak sanani tanlab bo‘lmaydi",
        "BACK": "🔙 Orqaga",
        "EXPIRED": "Kalendar klaviaturasi muddati tugagan",
    },
}


@dataclass
class CalendarResult:
    completed: bool
    chosen_date: Optional[date] = None


class CalendarCB(CallbackData, prefix="aiogramx_calendar"):
    action: str
    year: int = 0
    month: int = 0
    day: int = 0
    key: str = ""


class Calendar:
    _cb = CalendarCB
    __storage: dict[str, "Calendar"] = LRUDict(max_items=1000)
    __registered__: bool = False

    def __init__(
        self,
        max_range: Optional[timedelta] = None,
        can_select_past: bool = True,
        show_quick_buttons: bool = False,
        on_select: Optional[Callable[[CallbackQuery, date], Awaitable[None]]] = None,
        on_back: Optional[Callable[[CallbackQuery], Awaitable[None]]] = None,
        on_action_remove_kb: bool = False,
        lang: LangCode = "EN",
        warn_past_text: Optional[str] = None,
        warn_future_text: Optional[str] = None,
    ):
        if lang not in __TEXTS__:
            raise ValueError(f"Unsupported language code: {lang}")

        self.max_range = max_range
        self._can_select_past = can_select_past
        self._remove_kb_on_action = on_action_remove_kb
        self._show_quick_buttons = show_quick_buttons
        self.on_select = on_select
        self.on_back = on_back

        self.lang = lang
        self._warn_past_txt = warn_past_text or self._t("WARN_PAST")
        self._warn_future_txt = warn_future_text or self._t("WARN_FUTURE")
        self.__key = gen_key(self.__storage, length=4)
        self.__storage[self.__key] = self

        self._ignore_cb = self._cb(action="IGNORE", key=self.__key).pack()
        self._warn_past_cb = self._cb(action="WARN_PAST", key=self.__key).pack()
        self._warn_future_cb = self._cb(action="WARN_FUTURE", key=self.__key).pack()

    @classmethod
    def filter(cls):
        return cls._cb.filter()

    @classmethod
    def from_cb(cls, callback_data: CalendarCB) -> Optional["Calendar"]:
        return cls.__storage.get(callback_data.key)

    @classmethod
    def register(cls, router: Router):
        if cls.__registered__:
            return

        async def _handle(c: CallbackQuery, callback_data: CalendarCB):
            cl = cls.from_cb(callback_data)
            if not cl:
                # await c.answer(cl._t("EXPIRED"))
                await c.answer("Calendar keyboard is expired")

                await c.message.delete_reply_markup()
                return

            await cl.process_cb(c, callback_data)

        router.callback_query.register(_handle, cls.filter())
        cls.__registered__ = True

    @property
    def cb(self):
        return self._cb

    def _t(self, text_id: str) -> Union[str, list[str]]:
        return __TEXTS__[self.lang][text_id.upper()]

    async def render_kb(
        self, year: Optional[int] = None, month: Optional[int] = None
    ) -> InlineKeyboardMarkup:
        """
        Creates an inline keyboard with the provided year and month
        :param int year: Year to use in the calendar, if None the current year is used.
        :param int month: Month to use in the calendar, if None the current month is used.
        :return: Returns InlineKeyboardMarkup object with the calendar.
        """
        today = date.today()
        year = today.year if year is None else year
        month = today.month if month is None else month

        kb = InlineKeyboardBuilder()
        empty_btn = ibtn(text="  ", cb=self._ignore_cb)
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
                        key=self.__key,
                    ),
                ),
                ibtn(
                    text=self._t("TOMORROW"),
                    cb=self._cb(
                        action="DAY",
                        year=tomorrow.year,
                        month=tomorrow.month,
                        day=tomorrow.day,
                        key=self.__key,
                    ),
                ),
                ibtn(
                    text=self._t("OVERMORROW"),
                    cb=self._cb(
                        action="DAY",
                        year=overmorrow.year,
                        month=overmorrow.month,
                        day=overmorrow.day,
                        key=self.__key,
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
                    key=self.__key,
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
                    key=self.__key,
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
                    key=self.__key,
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
                    key=self.__key,
                ),
            )

        # Days of month
        days_kb = InlineKeyboardBuilder()

        for week in calendar.monthcalendar(year, month):
            for day in week:
                if day == 0:
                    days_kb.add(ibtn(" ", self._ignore_cb))
                    continue

                dt = date(year=year, month=month, day=day)

                if dt < today and not self._can_select_past:
                    cb = self._warn_past_cb
                elif self.max_range and dt > today and dt - today > self.max_range:
                    cb = self._warn_future_cb
                else:
                    cb = self._cb(
                        action="DAY",
                        year=year,
                        month=month,
                        day=day,
                        key=self.__key,
                    )

                is_today = (
                    day == today.day and month == today.month and year == today.year
                )
                days_kb.add(ibtn(text=f"• {day} •" if is_today else str(day), cb=cb))

        days_kb.adjust(7)

        # Build Keyboard
        # Month Controls
        kb.row(
            prev_month_btn,
            ibtn(f"{calendar.month_name[month]} {str(year)}", cb=self._ignore_cb),
            next_month_btn,
        )

        # Week Day Names
        kb.row(*[ibtn(day_name, cb=self._ignore_cb) for day_name in self._t("WEEKS")])

        # Days of month
        kb.attach(days_kb)

        # Year Controls
        kb.row(
            prev_year_btn,
            empty_btn,
            next_year_btn,
        )

        # Back Navigator
        kb.row(
            ibtn(
                self._t("BACK"),
                self._cb(
                    action="BACK",
                    key=self.__key,
                ),
            )
        )
        return kb.as_markup()

    async def process_cb(
        self, c: CallbackQuery, data: CalendarCB
    ) -> Optional[CalendarResult]:
        """
        Process the callback_query. This method generates a new calendar if forward or
        backward is pressed. This method should be called inside a CallbackQueryHandler.
        :param c: callback_query, as provided by the CallbackQueryHandler
        :param data: callback_data, dictionary, set by calendar_callback
        :return: Returns CalendarResult indicating if a date is selected
                    and returning the date if so.
        """
        result = CalendarResult(completed=False, chosen_date=None)

        if data.action == "IGNORE":
            await c.answer(cache_time=60)
            return result

        elif data.action == "WARN_PAST":
            await c.answer(self._warn_past_txt, show_alert=True)
            return result

        elif data.action == "WARN_FUTURE":
            await c.answer(self._warn_future_txt, show_alert=True)
            return result

        elif data.action == "CANCEL":
            if self._remove_kb_on_action:
                async with silent_fail():
                    await c.message.delete_reply_markup(request_timeout=1)
                await c.answer()

            if self.on_back:
                await self.on_back(c)
                return None

            return CalendarResult(completed=True, chosen_date=None)

        temp_date = date(data.year, data.month, 1)

        # user picked a day button, return date
        if data.action == "DAY":
            if self._remove_kb_on_action:
                async with silent_fail():
                    await c.message.delete_reply_markup(request_timeout=1)
                await c.answer()

            if self.on_select:
                await self.on_select(c, date(data.year, data.month, data.day))
                return None

            result = CalendarResult(
                completed=True, chosen_date=date(data.year, data.month, data.day)
            )

        # user navigates to previous year, editing message with new calendar
        elif data.action == "PREV-YEAR":
            prev_date = temp_date - timedelta(days=365)
            await c.message.edit_reply_markup(
                reply_markup=await self.render_kb(prev_date.year, prev_date.month)
            )

        # user navigates to next year, editing message with new calendar
        elif data.action == "NEXT-YEAR":
            next_date = temp_date + timedelta(days=365)
            await c.message.edit_reply_markup(
                reply_markup=await self.render_kb(next_date.year, next_date.month)
            )

        # user navigates to previous month, editing message with new calendar
        elif data.action == "PREV-MONTH":
            prev_date = temp_date - timedelta(days=1)
            await c.message.edit_reply_markup(
                reply_markup=await self.render_kb(prev_date.year, prev_date.month)
            )

        # user navigates to next month, editing message with new calendar
        elif data.action == "NEXT-MONTH":
            next_date = temp_date + timedelta(days=31)
            await c.message.edit_reply_markup(
                reply_markup=await self.render_kb(next_date.year, next_date.month)
            )

        return result
