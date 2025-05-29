from abc import abstractmethod, ABCMeta
from typing import Optional, TypeVar, Generic, Type, Dict

from aiogram import Router
from aiogram.types import CallbackQuery
from aiogram.filters.callback_data import CallbackData
from flipcache import LRUDict

from aiogramx.utils import gen_key


TCallbackData = TypeVar("TCallbackData", bound=CallbackData)
TWidget = TypeVar("TWidget", bound="WidgetBase")


class WidgetMeta(ABCMeta):
    """
    Metaclass for all AiogramX widgets.

    Ensures that subclasses of `WidgetBase` define a `_cb` attribute which must be a subclass of `CallbackData`
    and contain a `key` field used to identify instances.

    This metaclass enforces a contract that each widget must implement a specific structure for callback data.

    Raises:
        TypeError: If `_cb` is not defined, not a subclass of `CallbackData`, or missing a `key` attribute.
    """

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
    """
    Base class for building interactive widgets with Aiogram using callback queries and inline keyboards.

    Widgets subclassing `WidgetBase` must define a `_cb` class attribute which inherits from `CallbackData`
    and includes a `key` field to uniquely identify widget instances.

    Features:
    - Automatic widget instance tracking via LRU storage.
    - Simplified callback routing with auto-registration.
    - Safe handling of expired widgets.
    - Extensible design for building custom interactive UI components.

    Type Parameters:
        TCallbackData: A subclass of `CallbackData` used for routing and identifying interactions.
        TWidget: The type of the widget subclass.

    Attributes:
        _registered (bool): Indicates whether this widget class has been registered with a router.
    """

    _cb: TCallbackData
    _storage: Dict[str, TWidget]
    _registered: bool = False

    def __init_subclass__(cls, **kwargs):
        """
        Automatically initializes an LRU-based storage for the widget subclass,
        used to store and retrieve active widget instances.
        """
        super().__init_subclass__(**kwargs)
        # Auto-define _storage per subclass
        cls._storage: Dict[str, TWidget] = LRUDict(max_items=1000)

    def __init__(self):
        """
        Initializes a new widget instance with a unique key and registers it in the class-level storage.
        """
        self._key = gen_key(self.__class__._storage, length=4)
        self.__class__._storage[self._key] = self

    @classmethod
    def from_cb(cls: Type[TWidget], callback_data: TCallbackData) -> Optional[TWidget]:
        """
        Retrieves a widget instance based on the callback data's key.

        Args:
            callback_data (TCallbackData): Callback data containing a unique key.

        Returns:
            Optional[TWidget]: The corresponding widget instance, if found.
        """
        return cls._storage.get(callback_data.key)

    @property
    def cb(self):
        """
        Returns the callback data class associated with this widget.

        Returns:
            TCallbackData: The callback data class.
        """
        return self._cb

    @classmethod
    def filter(cls):
        """
        Returns the filter for processing callback queries for this widget.

        Returns:
            aiogram.filters.callback_data.CallbackDataFilter: The filter for the widget's callback data.
        """
        return cls._cb.filter()

    @classmethod
    def register(cls, router: Router) -> None:
        """
        Registers this widget with an Aiogram router. Hooks into the callback query event
        and dispatches control to the widget instance if found, or shows an expired message otherwise.

        Args:
            router (aiogram.Router): The router to register the callback handler with.
        """
        if cls._registered:
            return

        async def _handle(c: CallbackQuery, callback_data: TCallbackData):
            instance = cls.from_cb(callback_data)
            if not instance:
                await c.answer(cls.get_expired_text(c.from_user.language_code or "en"))
                await c.message.delete_reply_markup()
                return
            await instance.process_cb(c, callback_data)

        router.callback_query.register(_handle, cls.filter())
        cls._registered = True

    @property
    def is_registered(self) -> bool:
        """
        Indicates whether this widget's class has been registered with a router.

        This property checks the `_registered` class-level flag to determine if the widget type
        has already been registered via the `register()` method. Note that this reflects registration
        status at the class level, not per instance.

        Returns:
            bool: True if the widget's class is registered, False otherwise.
        """
        return self.__class__._registered

    @classmethod
    def get_expired_text(cls, lang: str = "en") -> str:
        """
        Returns a localized message shown when a user interacts with an expired widget.
        This method can be overridden in subclasses to customize the message.

        Args:
            lang (str): Language code, defaults to "en".

        Returns:
            str: Localized expired widget message.
        """
        return {
            "en": "This widget has expired.",
            "ru": "Этот виджет устарел.",
            "uz": "Bu vidjet eskirgan.",
        }.get(lang, "This widget has expired.")

    @abstractmethod
    async def process_cb(
        self, c: CallbackQuery, data: TCallbackData
    ) -> Optional[object]:
        """
        Abstract method to handle callback interactions for this widget instance.

        Must be implemented by subclasses to define how to respond to user actions.

        Args:
            c (CallbackQuery): The callback query event from the user.
            data (TCallbackData): Parsed callback data.

        Returns:
            Optional[object]: Return value can be used in standalone mode.
        """
        pass

    @abstractmethod
    async def render_kb(self):
        """
        Abstract method to render the widget's inline keyboard.
        This method must be implemented by subclasses to return the markup that represents the current UI state.

        Returns:
            InlineKeyboardMarkup: The inline keyboard markup for the widget.
        """
        pass
