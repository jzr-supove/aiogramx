import uuid
from math import ceil
from typing import Optional, List, Awaitable, Protocol, Callable

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder


storage = {}

class LazyButtonLoader(Protocol):
    def __call__(
        self, *, cur_page: int = ..., per_page: int = ...
    ) -> Awaitable[list[InlineKeyboardButton]]: ...


class PaginatorCB(CallbackData, prefix="aiogramx_pg"):
    action: str
    page: int = 1
    unique_hash: str = ""


class Paginator:
    cb = PaginatorCB
    pass_cb = PaginatorCB(action="PASS").pack()

    def __init__(
        self,
        data: List[InlineKeyboardButton] = None,
        lazy_data: Optional[LazyButtonLoader] = None,
        lazy_count: Optional[Callable[..., Awaitable[int]]] = None,
        per_page: int = 10,
        per_row: int = 1,
    ) -> None:
        if not (data or lazy_data):
            raise ValueError("You must provide either 'data' or 'lazy_data', not both.")

        if data and lazy_data:
            raise ValueError("Only one of 'data' or 'lazy_data' should be provided.")

        if lazy_data is not None and lazy_count is None:
            raise ValueError("'lazy_count' must be provided when 'lazy_data' is provided.")

        self.data = data
        self.count = len(data) if data is not None else None
        self.lazy_data = lazy_data
        self.lazy_count = lazy_count
        self.per_page = per_page
        self.per_row = per_row
        self.key = uuid.uuid4().hex
        storage[self.key] = self

    @classmethod
    def filter(cls):
        return PaginatorCB.filter()


    @classmethod
    def from_cb(cls, callback_data: PaginatorCB) -> Optional["Paginator"]:
        return storage.get(callback_data.unique_hash)

    @property
    def is_lazy(self) -> bool:
        return self.lazy_data is not None

    async def get_count(self):
        if self.count is None and self.is_lazy:
            self.count = await self.lazy_count()
        return self.count

    async def _get_page_items(
        self, builder: InlineKeyboardBuilder, cur_page: int
    ) -> None:
        start_idx = (cur_page - 1) * self.per_page
        end_idx = start_idx + self.per_page

        if self.is_lazy:
            items = await self.lazy_data(cur_page=cur_page, per_page=self.per_page)
        else:
            items = self.data[start_idx:end_idx]

        builder.add(*items)
        builder.adjust(self.per_row)

    async def _build_pagination_buttons(self, builder: InlineKeyboardBuilder, cur_page: int):
        last_page = ceil(await self.get_count() / self.per_page)
        empty_button = InlineKeyboardButton(text=" ", callback_data=self.pass_cb)

        if cur_page > 1:
            first = InlineKeyboardButton(
                text="<<",
                callback_data=self.cb(action="NAV", page=1, unique_hash=self.key).pack(),
            )
            left = InlineKeyboardButton(
                text="<",
                callback_data=self.cb(action="NAV", page=cur_page - 1, unique_hash=self.key).pack(),
            )
        else:
            first = empty_button
            left = empty_button

        info = InlineKeyboardButton(
            text=f"{cur_page} / {last_page}",
            callback_data=self.pass_cb,
        )

        if cur_page < last_page:
            right = InlineKeyboardButton(
                text=">",
                callback_data=self.cb(action="NAV", page=cur_page + 1, unique_hash=self.key).pack(),
            )
            last = InlineKeyboardButton(
                text=">>", callback_data=self.cb(action="NAV", page=last_page, unique_hash=self.key).pack()
            )
        else:
            right = empty_button
            last = empty_button

        builder.row(first, left, info, right, last)
        builder.row(
            InlineKeyboardButton(
                text="<-- Go Back", callback_data=self.cb(action="BACK").pack()
            )
        )

    async def render_kb(self, page: int = 1):
        builder = InlineKeyboardBuilder()
        await self._get_page_items(builder, page)
        await self._build_pagination_buttons(builder, page)
        return builder.as_markup()

    async def process_cb(self, c: CallbackQuery, data: PaginatorCB) -> bool:
        if data.action == "PASS":
            await c.answer(cache_time=120)

        elif data.action == "NAV":
            await c.message.edit_reply_markup(
                reply_markup=await self.render_kb(data.page)
            )
            await c.answer()

        elif data.action == "BACK":
            await c.answer(cache_time=120)
            return True

        return False
