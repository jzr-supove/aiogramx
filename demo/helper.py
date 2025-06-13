from typing import Optional


def extract_pager_data(input_str: Optional[str]) -> tuple[str, int, int]:
    valid_langs = {"en", "uz", "ru"}
    lang = "en"
    per_page = 10
    per_row = 1

    if input_str is None:
        return lang, per_page, per_row

    parts = input_str.strip().split()
    nums = []

    for part in parts:
        if part in valid_langs:
            lang = part
        elif part.isdigit():
            nums.append(int(part))

    if len(nums) >= 1:
        per_page = nums[0]
    if len(nums) >= 2:
        per_row = nums[1]

    return lang, per_page, per_row


def extract_time_selector_data(input_str: Optional[str]) -> tuple[str, str, bool, bool]:
    valid_langs = {"en", "uz", "ru"}
    valid_ts_types = {"modern", "grid"}
    lang = "en"
    ts_type = "modern"
    carry_over = False
    future_only = False

    if input_str is None:
        return lang, ts_type, future_only, carry_over

    parts = input_str.strip().split()
    for part in parts:
        if part in valid_langs:
            lang = part
        elif part in valid_ts_types:
            ts_type = part
        elif part in "carry_over":
            carry_over = True
        elif part == "future_only":
            future_only = True

    return lang, ts_type, future_only, carry_over


def boolmoji(value: bool) -> str:
    """
    Converts a boolean value to a corresponding emoji string.

    Args:
        value (bool): The boolean value to convert.

    Returns:
        str: "✅" for True, "❌" for False.
    """
    return "✅" if value else "❌"


def langmoji(lang: str) -> str:
    """
    Converts a language code to a corresponding emoji string.

    Args:
        lang (str): The language code to convert.

    Returns:
        str: "🇺🇿" for "uz", "🇷🇺" for "ru", "🇬🇧" for "en".
    """
    return {"uz": "🇺🇿", "ru": "🇷🇺", "en": "🇬🇧"}.get(lang, "❓")


if __name__ == "__main__":
    print(extract_pager_data(""))  # ('en', 10, 1)
    print(extract_pager_data("uz 12 10"))  # ('uz', 12, 10)
    print(extract_pager_data("uz"))  # ('uz', 10, 1)
    print(extract_pager_data("ru 25"))  # ('ru', 25, 1)
    print(extract_pager_data("9 3"))  # ('en', 9, 3)
