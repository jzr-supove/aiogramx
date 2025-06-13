from aiogram.types import KeyboardButton, ReplyKeyboardRemove
from aiogram.types import ReplyKeyboardMarkup


class ReplyKeyboardMeta(type):
    """Metaclass for creating static reply keyboards with predefined button layouts.

    This metaclass allows defining keyboard buttons directly as class attributes,
    which are then used to construct a `ReplyKeyboardMarkup` instance. Optionally,
    a custom layout can be provided using a special `__LAYOUT__` attribute.

    Use by setting `metaclass=ReplyKeyboardMeta` in your class definition and passing
    optional class-keyword arguments.

    Class-keyword arguments:
        is_persistent (bool, optional): Whether the keyboard should remain visible after use.
        resize_keyboard (bool, optional): Whether the keyboard should resize to fit the screen (default: True).
        one_time_keyboard (bool, optional): Whether to hide the keyboard after it's used.
        input_field_placeholder (str, optional): Placeholder text for the input field.
        selective (bool, optional): Whether to show the keyboard to specific users only.

    Example:
        class MyKeyboard(metaclass=ReplyKeyboardMeta, input_field_placeholder="Type..."):
            GREET = "👋 Hello"
            BYE = "👋 Bye"
            ASK = "❓ Ask"

            __LAYOUT__ = [
                [GREET, BYE],
                [ASK]
            ]
    """

    _button_set: set
    _kb: ReplyKeyboardMarkup

    def __new__(mcs, name, bases, namespace, **kwargs):
        """Create a new class with a predefined reply keyboard layout.

        Args:
            name (str): The name of the class.
            bases (tuple): A tuple of base classes.
            namespace (dict): The class namespace dictionary.
            **kwargs: Additional keyword arguments for keyboard configuration.

        Keyword Args:
            is_persistent (bool, optional): Whether the keyboard should be persistent.
            resize_keyboard (bool, optional): Whether the keyboard should be resized to fit.
            one_time_keyboard (bool, optional): Whether the keyboard should be hidden after use.
            input_field_placeholder (str, optional): Placeholder text for the input field.
            selective (bool, optional): Whether to show the keyboard to specific users.

        Returns:
            type: A new class with the reply keyboard metadata.
        """
        namespace["__slots__"] = ()

        buttons = [
            v
            for k, v in namespace.items()
            if not k.startswith("_") and isinstance(v, str)
        ]
        namespace["_button_set"] = set(buttons)

        if layout := namespace.get("__LAYOUT__"):
            keyboard = []
            for row in layout:
                kb_row = [KeyboardButton(text=col) for col in row]
                keyboard.append(kb_row)
            del namespace["__LAYOUT__"]
        else:
            keyboard = [[KeyboardButton(text=b)] for b in buttons]

        namespace["_kb"] = ReplyKeyboardMarkup(
            keyboard=keyboard,
            is_persistent=kwargs.get("is_persistent", None),
            resize_keyboard=kwargs.get("resize_keyboard", True),
            one_time_keyboard=kwargs.get("one_time_keyboard", None),
            input_field_placeholder=kwargs.get("input_field_placeholder", None),
            selective=kwargs.get("selective", None),
        )

        return super().__new__(mcs, name, bases, namespace)

    def __setattr__(cls, key, value):
        """Prevent setting attributes on the class.

        Raises:
            AttributeError: Always raised to prevent modification.
        """
        raise AttributeError(f"'{cls.__name__}' attributes are read-only")

    def __contains__(cls, item):
        """Check if a button label is in the keyboard.

        Args:
            item (str): The button label to check.

        Returns:
            bool: True if the label exists, False otherwise.
        """
        return item in cls._button_set

    def __iter__(cls):
        """Iterate over all button labels.

        Yields:
            str: Each button label.
        """
        for button in cls._button_set:
            yield button

    def __getitem__(cls, index: int):
        """Get a button label by its index.

        Args:
            index (int): The index of the button.

        Returns:
            str: The button label at the given index.

        Raises:
            TypeError: If the index is not an integer.
        """
        if not isinstance(index, int):
            raise TypeError("Index must be an integer")

        return tuple(cls)[index]

    @property
    def kb(cls):
        """ReplyKeyboardMarkup: The constructed reply keyboard."""
        return cls._kb

    @property
    def remove(cls):
        """ReplyKeyboardRemove: An instance used to remove the reply keyboard."""
        return ReplyKeyboardRemove()
