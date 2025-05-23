from abc import abstractmethod, ABCMeta
from typing import Optional, TypeVar, Generic, Type, Dict
from aiogram.types import CallbackQuery
from aiogram.filters.callback_data import CallbackData
from flipcache import LRUDict

from aiogramx.utils import gen_key


TCallbackData = TypeVar("TCallbackData", bound=CallbackData)
TWidget = TypeVar("TWidget", bound="WidgetBase")


class WidgetMeta(ABCMeta):
    def __init__(cls, name, bases, namespace, **kwargs):
        super().__init__(name, bases, namespace)

        # Skip check for base class itself
        if cls.__name__ == "WidgetBase":
            return

        # Ensure _cb is defined and is a CallbackData subclass
        cb = getattr(cls, "_cb", None)
        if cb is None:
            raise TypeError(f"{cls.__name__} must define a '_cb' attribute.")

        if not issubclass(cb, CallbackData):
            raise TypeError(
                f"_cb must be a subclass of CallbackData in {cls.__name__}, got {cb}"
            )

        # Ensure _cb has 'key' attribute
        if "key" not in cb.model_fields:
            raise TypeError(f"{cls.__name__}._cb must define a 'key' attribute.")


class WidgetBase(Generic[TCallbackData, TWidget], metaclass=WidgetMeta):
    _cb: TCallbackData
    _storage: Dict[str, TWidget]
    __registered__: bool = False

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # Auto-define _storage per subclass
        cls._storage: Dict[str, TWidget] = LRUDict(max_items=1000)

    def __init__(self):
        self._key = gen_key(self.__class__._storage, length=4)
        self.__class__._storage[self._key] = self

    @classmethod
    def from_cb(cls: Type[TWidget], callback_data: TCallbackData) -> Optional[TWidget]:
        return cls._storage.get(callback_data.key)

    @classmethod
    def filter(cls):
        return cls._cb.filter()

    @classmethod
    def register(cls, router):
        if cls.__registered__:
            return

        async def _handle(c: CallbackQuery, callback_data: TCallbackData):
            instance = cls.from_cb(callback_data)
            if not instance:
                await c.answer(cls.get_expired_text())
                await c.message.delete_reply_markup()
                return
            await instance.process_cb(c, callback_data)

        router.callback_query.register(_handle, cls.filter())
        cls.__registered__ = True

    @classmethod
    def get_expired_text(cls) -> str:
        return "This widget has expired."

    @abstractmethod
    async def process_cb(
        self, c: CallbackQuery, data: TCallbackData
    ) -> Optional[object]:
        pass
