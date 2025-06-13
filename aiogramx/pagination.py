from math import ceil
from typing import Optional, List, Awaitable, Protocol, Callable

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, CallbackQuery, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from aiogramx.base import WidgetBase
from aiogramx.utils import ibtn, fallback_lang


_TEXTS = {
    "en": {"back": "🔙 Back"},
    "ru": {"back": "🔙 Назад"},
    "uz": {"back": "🔙 Orqaga"},
}


class LazyButtonLoader(Protocol):
    def __call__(
        self, *, cur_page: int = ..., per_page: int = ...
    ) -> Awaitable[list[InlineKeyboardButton]]:
        """Protocol for lazy-loading buttons in a paginator.

        A callable that accepts keyword arguments `cur_page` and `per_page`
        and returns a list of InlineKeyboardButton objects asynchronously.

        Args:
            cur_page (int): Current page number.
            per_page (int): Number of items per page.

        Returns:
            Awaitable[list[InlineKeyboardButton]]: List of buttons for the specified page.
        """
        ...


class PaginatorCB(CallbackData, prefix="aiogramx_pg"):
    """Callback data structure for paginator interactions.

    Attributes:
        action (str): Action type (e.g., NAV, BACK, SEL, PASS).
        data (str): Payload data, such as page number or button-specific data.
        key (str): Identifier key for widget instance tracking.
    """

    action: str
    data: str = ""
    key: str = ""


class Paginator(WidgetBase[PaginatorCB, "Paginator"]):
    """
    An inline keyboard paginator for Aiogram with optional lazy-loading support.

    Supports dynamic or static data rendering with customizable pagination,
    selection handling, and back navigation.

    Args:
        per_page (int): Number of items per page (default is 10).
        per_row (int): Number of items per row (default is 1).
        data (Optional[List[InlineKeyboardButton]]): Static list of buttons.
        lazy_data (Optional[LazyButtonLoader]):
            Async function to lazily load buttons for a given page.
            Function must accept two integer arguments: `cur_page` and `per_page`
        lazy_count (Optional[Callable[..., Awaitable[int]]]):
            Async function to return total number of buttons for lazy mode.
            Required when `lazy_data` is provided.
        on_select (Optional[Callable[[CallbackQuery, str], Awaitable[None]]]):
            When provided, wraps content buttons with paginator's callback data.
            Callback function to be triggered when a content button is clicked.
            The second argument is the original `callback_data` from the button.
        on_back (Optional[Callable[[CallbackQuery], Awaitable[None]]]):
            Callback function to be triggered when the "Go Back" button is pressed.
        back_button_text (Optional[str]): Custom label for the "Back" button.

    Raises:
        ValueError: If both or neither `data` and `lazy_data` are provided.
        ValueError: If `lazy_data` is used without `lazy_count`.
        ValueError: If `per_page` or `per_row` are non-positive.
    """

    _cb = PaginatorCB

    def __init__(
        self,
        per_page: int = 10,
        per_row: int = 1,
        data: Optional[List[InlineKeyboardButton]] = None,
        lazy_data: Optional[LazyButtonLoader] = None,
        lazy_count: Optional[Callable[..., Awaitable[int]]] = None,
        on_select: Optional[Callable[[CallbackQuery, str], Awaitable[None]]] = None,
        on_back: Optional[Callable[[CallbackQuery], Awaitable[None]]] = None,
        lang: Optional[str] = "en",
        back_button_text: Optional[str] = None,
    ) -> None:
        if not (data or lazy_data):
            raise ValueError("You must provide either 'data' or 'lazy_data', not both.")

        if data and lazy_data:
            raise ValueError("Only one of 'data' or 'lazy_data' should be provided.")

        if lazy_data is not None and lazy_count is None:
            raise ValueError(
                "'lazy_count' must be provided when 'lazy_data' is provided."
            )

        # Validate per_row
        if not (1 <= per_row <= 8):
            raise ValueError("per_row must be between 1 and 8")

        # Validate per_page
        if not (1 <= per_page <= 94):
            raise ValueError("per_page must be between 1 and 94")

        self.per_page = per_page
        self.per_row = per_row
        self._data = data
        self._count = len(data) if data is not None else None
        self._lazy_data = lazy_data
        self._lazy_count = lazy_count

        self.on_select = on_select
        self.on_back = on_back
        self.lang = fallback_lang(lang)
        self._back_button_text = back_button_text or _TEXTS[self.lang]["back"]

        super().__init__()

    def _(self, action: str, data: str = "") -> str:
        """
        Packs callback data into a string with key implicitly.

        Args:
            action (str): Action type (NAV, SEL, etc.).
            data (str): Additional string data.

        Returns:
            str: Packed callback data string.
        """
        return self._cb(action=action, data=data, key=self._key).pack()

    @property
    def is_lazy(self) -> bool:
        """
        Check if paginator is in lazy-loading mode.

        Returns:
            bool: True if lazy-loading is enabled, False otherwise.
        """
        return self._lazy_data is not None

    async def get_count(self) -> int:
        """
        Retrieve total number of items for pagination.

        Returns:
            int: Total item count, either static or from lazy source.
        """
        if self._count is None and self.is_lazy:
            self._count = await self._lazy_count()
        return self._count

    async def _get_page_items(
        self, builder: InlineKeyboardBuilder, cur_page: int
    ) -> None:
        """
        Populates the keyboard builder with items for the current page.

        Args:
            builder (InlineKeyboardBuilder): The builder to which buttons are added.
            cur_page (int): The page number to render.
        """
        start_idx = (cur_page - 1) * self.per_page
        end_idx = start_idx + self.per_page

        if self.is_lazy:
            items = await self._lazy_data(cur_page=cur_page, per_page=self.per_page)
        else:
            items = self._data[start_idx:end_idx]

        if self.on_select:
            for b in items:
                if not b.callback_data.endswith(self._key):
                    b.callback_data = self._("SEL", b.callback_data)

        builder.add(*items)
        builder.adjust(self.per_row)

    async def _build_pagination_buttons(
        self, builder: InlineKeyboardBuilder, cur_page: int
    ) -> None:
        """
        Appends pagination navigation buttons to the builder.

        Args:
            builder (InlineKeyboardBuilder): The builder to which navigation buttons are added.
            cur_page (int): Current page number.
        """
        last_page = ceil(await self.get_count() / self.per_page)
        pass_cb = self._(action="PASS")
        empty_button = ibtn(text=" ", cb=pass_cb)
        first = left = right = last = empty_button

        if cur_page > 1:
            first = ibtn(text="<<", cb=self._("NAV", "1"))
            left = ibtn(text="<", cb=self._("NAV", str(cur_page - 1)))

        info = ibtn(text=f"{cur_page} / {last_page}", cb=pass_cb)

        if cur_page < last_page:
            right = ibtn(text=">", cb=self._(action="NAV", data=str(cur_page + 1)))
            last = ibtn(text=">>", cb=self._(action="NAV", data=str(last_page)))

        builder.row(first, left, info, right, last)
        if self.on_back:
            builder.row(ibtn(text=self._back_button_text, cb=self._(action="BACK")))

    async def render_kb(self, page: int = 1) -> InlineKeyboardMarkup:
        """Renders the complete inline keyboard for a given page.

        Args:
            page (int): Page number to render. Defaults to 1.

        Returns:
            InlineKeyboardMarkup: Inline keyboard markup with items and navigation.
        """
        builder = InlineKeyboardBuilder()
        await self._get_page_items(builder, page)
        await self._build_pagination_buttons(builder, page)
        return builder.as_markup()

    async def process_cb(
        self, c: CallbackQuery, data: PaginatorCB
    ) -> Optional[PaginatorCB]:
        """Processes a paginator callback query.

        Handles navigation, selection, and back actions.

        Args:
            c (CallbackQuery): Incoming callback query.
            data (PaginatorCB): Parsed paginator callback data.

        Returns:
            Optional[PaginatorCB]: Callback data for further use, or None if handled internally.
        """
        if data.action == "PASS":
            await c.answer(cache_time=120)

        elif data.action == "NAV":
            page = int(data.data)
            await c.message.edit_reply_markup(reply_markup=await self.render_kb(page))
            await c.answer()

        elif data.action == "BACK":
            if self.on_back:
                await self.on_back(c)
            elif self.is_registered:
                await c.message.edit_text("Ok")
                await c.answer()
            else:
                return data

        elif data.action == "SEL":
            if self.on_select:
                await self.on_select(c, data.data)
            elif self.is_registered:
                pass
            else:
                return data

        return None
