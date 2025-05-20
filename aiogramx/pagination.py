from math import ceil
from typing import Optional, List, Awaitable, Protocol, Callable, Union

from aiogram import Router
from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from aiogramx.utils import gen_key, ibtn
from flipcache import LRUDict


class LazyButtonLoader(Protocol):
    def __call__(
        self, *, cur_page: int = ..., per_page: int = ...
    ) -> Awaitable[list[InlineKeyboardButton]]: ...


class PaginatorCB(CallbackData, prefix="aiogramx_pg"):
    action: str  # NAV, BACK, SEL, PASS
    data: str = ""
    key: str = ""


class Paginator:
    cb = PaginatorCB
    __storage__: dict[str, "Paginator"] = LRUDict()
    __registered__: bool = False

    def __init__(
        self,
        per_page: int = 10,
        per_row: int = 1,
        data: Optional[List[InlineKeyboardButton]] = None,
        lazy_data: Optional[LazyButtonLoader] = None,
        lazy_count: Optional[Callable[..., Awaitable[int]]] = None,
        on_select: Optional[Callable[[CallbackQuery, str], Awaitable[None]]] = None,
        on_back: Optional[Callable[[CallbackQuery], Awaitable[None]]] = None,
    ) -> None:
        """
        Create a new paginated inline keyboard interface.

        Supports both static and lazy-loading button sources, with optional
        callback handlers for selection and "Go Back" navigation.

        Parameters
        ----------
        per_page : int, optional
            Number of buttons to display per page (default is 10).
        per_row : int, optional
            Number of buttons per row (default is 1).
        data : list[InlineKeyboardButton], optional
            Preloaded list of buttons for pagination (static mode).
        lazy_data : Callable[..., Awaitable[list[InlineKeyboardButton]]], optional
            Async function to fetch buttons for a given page (lazy mode).
            Function must accept two integer arguments: `cur_page` and `per_page`
        lazy_count : Callable[..., Awaitable[int]], optional
            Async function to return the total number of buttons available.
            Required when using `lazy_data`.
        on_select : Callable[[CallbackQuery, str], Awaitable[None]], optional
            When provided, wraps content buttons with paginator's callback data.
            Callback function is triggered when a content button is clicked.
            The second argument is the original `callback_data` from the button.
        on_back : Callable[[CallbackQuery], Awaitable[None]], optional
            Callback function is triggered when the "Go Back" button is pressed.

        Raises
        ------
        ValueError
            If both or neither of `data` and `lazy_data` are provided.
        ValueError
            If `lazy_data` is provided without `lazy_count`.
        ValueError
            If `per_page` or `per_row` are not positive integers.
        """

        if not (data or lazy_data):
            raise ValueError("You must provide either 'data' or 'lazy_data', not both.")

        if data and lazy_data:
            raise ValueError("Only one of 'data' or 'lazy_data' should be provided.")

        if lazy_data is not None and lazy_count is None:
            raise ValueError(
                "'lazy_count' must be provided when 'lazy_data' is provided."
            )

        if per_page <= 0 or per_row <= 0:
            raise ValueError("'per_page' and 'per_row' must be positive integers.")

        self.per_page = per_page
        self.per_row = per_row
        self._data = data
        self._count = len(data) if data is not None else None
        self._lazy_data = lazy_data
        self._lazy_count = lazy_count
        self.__key__ = gen_key(self.__storage__, length=5)
        self.__storage__[self.__key__] = self

        self.on_select = on_select
        self.on_back = on_back

    def _(self, action: str, data: str = "") -> str:
        return self.cb(action=action, data=data, key=self.__key__).pack()

    @classmethod
    def filter(cls):
        return PaginatorCB.filter()

    @classmethod
    def from_cb(cls, callback_data: PaginatorCB) -> Optional["Paginator"]:
        return cls.__storage__.get(callback_data.key)

    @property
    def is_lazy(self) -> bool:
        return self._lazy_data is not None

    async def get_count(self):
        if self._count is None and self.is_lazy:
            self._count = await self._lazy_count()
        return self._count

    async def _get_page_items(
        self, builder: InlineKeyboardBuilder, cur_page: int
    ) -> None:
        start_idx = (cur_page - 1) * self.per_page
        end_idx = start_idx + self.per_page

        if self.is_lazy:
            items = await self._lazy_data(cur_page=cur_page, per_page=self.per_page)
        else:
            items = self._data[start_idx:end_idx]

        if self.on_select:
            for b in items:
                if not b.callback_data.endswith(self.__key__):
                    b.callback_data = self._("SEL", b.callback_data)

        builder.add(*items)
        builder.adjust(self.per_row)

    async def _build_pagination_buttons(
        self, builder: InlineKeyboardBuilder, cur_page: int
    ):
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
            builder.row(ibtn(text="🔙 Go Back", cb=self._(action="BACK")))

    async def render_kb(self, page: int = 1):
        if self.__key__ not in self.__storage__:
            self.__storage__[self.__key__] = self

        builder = InlineKeyboardBuilder()
        await self._get_page_items(builder, page)
        await self._build_pagination_buttons(builder, page)
        return builder.as_markup()

    async def process_cb(
        self, c: CallbackQuery, data: PaginatorCB
    ) -> Union[PaginatorCB, None]:
        if data.action == "PASS":
            await c.answer(cache_time=120)

        elif data.action == "NAV":
            page = int(data.data)
            await c.message.edit_reply_markup(reply_markup=await self.render_kb(page))
            await c.answer()

        elif data.action == "BACK":
            if self.on_back:
                await self.on_back(c)
                await c.answer()
            return data

        elif data.action == "SEL":
            if self.on_select:
                await self.on_select(c, data.data)
                await c.answer()
            return data

        return None

    @classmethod
    def register(cls, router: Router):
        """
        Register a default callback handler for all Paginator instances.

        This sets up the router to handle `CallbackQuery` events that match
        the paginator's callback data filter. The handler will automatically
        retrieve the appropriate Paginator instance from storage and process
        the callback using `process_cb`.

        This method ensures that the handler is only registered once per runtime,
        using the `__registered__` flag to prevent duplicate registrations.

        Parameters
        ----------
        router : Router
            The Aiogram router to register the callback handler with.
        """
        if cls.__registered__:
            return

        async def _handle(c: CallbackQuery, callback_data: PaginatorCB):
            paginator = cls.from_cb(callback_data)
            if not paginator:
                await c.answer("Paginator expired")
                await c.message.delete_reply_markup()
                return

            await paginator.process_cb(c, callback_data)

        router.callback_query.register(_handle, cls.filter())
        cls.__registered__ = True
