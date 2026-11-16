"""FX-3: unknown / missing language codes must fall back to English, never raise."""
import asyncio
from datetime import time
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.types import InlineKeyboardButton

from aiogramx import Calendar, Checkbox, Paginator, TimeSelectorGrid, TimeSelectorModern
from aiogramx.base import WidgetBase
from aiogramx.calendar import CalendarCB
from aiogramx.checkbox import CheckboxCB
from aiogramx.time_selector import TimeSelectorCB

UNKNOWN = ["de", "", None, "xx-YY", "EN"]
KNOWN = ["en", "ru", "uz"]
WIDGETS = [Calendar, Checkbox, Paginator, TimeSelectorGrid, TimeSelectorModern]


def _texts(markup):
    return [b.text for row in markup.inline_keyboard for b in row]


def _cb():
    c = MagicMock()
    c.answer = AsyncMock()
    c.message = MagicMock()
    c.message.edit_reply_markup = AsyncMock()
    c.message.edit_text = AsyncMock()
    c.message.delete = AsyncMock()
    return c


def _answered_text(c):
    c.answer.assert_awaited()
    return c.answer.await_args.args[0]


# ---- builders: (lang) -> widget -------------------------------------------
def _calendar(lang):
    return Calendar(lang=lang, show_quick_buttons=True)


def _checkbox(lang):
    return Checkbox(["a", "b"], lang=lang)


def _paginator(lang):
    data = [InlineKeyboardButton(text=str(i), callback_data=f"x{i}") for i in range(30)]
    return Paginator(per_page=5, data=data, lang=lang, on_back=AsyncMock())


def _grid(lang):
    return TimeSelectorGrid(lang=lang)


def _modern(lang):
    return TimeSelectorModern(lang=lang)


def _render(widget):
    out = widget.render_kb()
    if asyncio.iscoroutine(out):
        out = asyncio.run(out)
    return out


# ---- expired text -----------------------------------------------------------
@pytest.mark.parametrize("widget", WIDGETS)
@pytest.mark.parametrize("lang", UNKNOWN)
def test_get_expired_text_unknown_lang_falls_back_to_english(widget, lang):
    en = widget.get_expired_text("en")
    assert en  # sanity: english text is non-empty
    assert widget.get_expired_text(lang) == en


@pytest.mark.parametrize("widget", WIDGETS)
def test_get_expired_text_known_langs_are_localised(widget):
    texts = {lang: widget.get_expired_text(lang) for lang in KNOWN}
    assert len(set(texts.values())) == 3, texts


def test_calendar_expired_text_default_arg_is_english():
    assert Calendar.get_expired_text() == Calendar.get_expired_text("en")


def test_base_expired_text_unknown_lang_is_english():
    assert WidgetBase.get_expired_text("de") == "This widget has expired."


# ---- constructor + render ---------------------------------------------------
@pytest.mark.parametrize("build", [_calendar, _checkbox, _paginator, _grid, _modern])
@pytest.mark.parametrize("lang", UNKNOWN)
def test_render_with_unknown_lang_matches_english(build, lang):
    assert _texts(_render(build(lang))) == _texts(_render(build("en")))


@pytest.mark.parametrize("build", [_calendar, _checkbox, _paginator])
@pytest.mark.parametrize("lang", ["ru", "uz"])
def test_render_known_langs_keep_own_text(build, lang):
    # these widgets have localised back/done/weekday labels visible in the keyboard
    assert _texts(_render(build(lang))) != _texts(_render(build("en")))


# ---- user-visible alerts raised from process_cb -----------------------------
@pytest.mark.parametrize("lang", UNKNOWN)
def test_checkbox_at_least_one_alert_falls_back(lang):
    async def run(lang):
        w = Checkbox(["a"], lang=lang)
        c = _cb()
        await w.process_cb(c, CheckboxCB(action="DONE", key=w._key))
        return _answered_text(c)

    assert asyncio.run(run(lang)) == asyncio.run(run("en"))


@pytest.mark.parametrize("lang", ["ru", "uz"])
def test_checkbox_at_least_one_alert_known_lang_differs(lang):
    async def run(lang):
        w = Checkbox(["a"], lang=lang)
        c = _cb()
        await w.process_cb(c, CheckboxCB(action="DONE", key=w._key))
        return _answered_text(c)

    assert asyncio.run(run(lang)) != asyncio.run(run("en"))


@pytest.mark.parametrize("action", ["WARN_PAST", "WARN_FUTURE"])
@pytest.mark.parametrize("lang", UNKNOWN)
def test_calendar_warnings_fall_back(action, lang):
    async def run(lang):
        w = Calendar(lang=lang)
        c = _cb()
        await w.process_cb(c, CalendarCB(action=action, key=w._key))
        return _answered_text(c)

    assert asyncio.run(run(lang)) == asyncio.run(run("en"))


@pytest.mark.parametrize("cls", [TimeSelectorGrid, TimeSelectorModern])
@pytest.mark.parametrize("lang", UNKNOWN)
def test_time_selector_past_warning_falls_back(cls, lang):
    async def run(lang):
        w = cls(lang=lang, allow_future_only=True)
        c = _cb()
        await w.process_cb(c, TimeSelectorCB(act="DONE", hour=0, minute=0, key=w._key))
        return _answered_text(c)

    en = asyncio.run(run("en"))
    assert "past" in en.lower()
    assert asyncio.run(run(lang)) == en


@pytest.mark.parametrize("cls", [TimeSelectorGrid, TimeSelectorModern])
@pytest.mark.parametrize("lang", ["ru", "uz"])
def test_time_selector_past_warning_known_lang_differs(cls, lang):
    async def run(lang):
        w = cls(lang=lang, allow_future_only=True)
        c = _cb()
        await w.process_cb(c, TimeSelectorCB(act="DONE", hour=0, minute=0, key=w._key))
        return _answered_text(c)

    assert asyncio.run(run(lang)) != asyncio.run(run("en"))
