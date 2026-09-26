try:
    from wzgram.types import InlineKeyboardMarkup, InlineKeyboardButton
    from wzgram.enums import ButtonStyle
except ImportError:
    from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    try:
        from pyrogram.enums import ButtonStyle
    except ImportError:
        class ButtonStyle:
            DEFAULT = "default"
            PRIMARY = "primary"
            DANGER = "danger"
            SUCCESS = "success"


def _make_button(text, url=None, callback_data=None, style=None):
    kwargs = {"text": text}
    if url is not None:
        kwargs["url"] = url
    if callback_data is not None:
        kwargs["callback_data"] = callback_data
    if style is not None:
        kwargs["style"] = style
    try:
        return InlineKeyboardButton(**kwargs)
    except TypeError:
        kwargs.pop("style", None)
        return InlineKeyboardButton(**kwargs)


class ButtonMaker:
    def __init__(self):
        self._button = []
        self._header_button = []
        self._footer_button = []

    def url_button(self, key, link, position=None, style=ButtonStyle.DEFAULT):
        if style not in [
            ButtonStyle.DEFAULT,
            ButtonStyle.PRIMARY,
            ButtonStyle.DANGER,
            ButtonStyle.SUCCESS,
        ]:
            if style.lower() == "blue":
                style = ButtonStyle.PRIMARY
            elif style.lower() == "red":
                style = ButtonStyle.DANGER
            elif style.lower() == "green":
                style = ButtonStyle.SUCCESS
        btn = _make_button(text=key, url=link, style=style)
        if not position:
            self._button.append(btn)
        elif position == "header":
            self._header_button.append(btn)
        elif position == "footer":
            self._footer_button.append(btn)

    def data_button(self, key, data, position=None, style=ButtonStyle.DEFAULT):
        if style not in [
            ButtonStyle.DEFAULT,
            ButtonStyle.PRIMARY,
            ButtonStyle.DANGER,
            ButtonStyle.SUCCESS,
        ]:
            if style.lower() == "blue":
                style = ButtonStyle.PRIMARY
            elif style.lower() == "red":
                style = ButtonStyle.DANGER
            elif style.lower() == "green":
                style = ButtonStyle.SUCCESS
        btn = _make_button(text=key, callback_data=data, style=style)
        if not position:
            self._button.append(btn)
        elif position == "header":
            self._header_button.append(btn)
        elif position == "footer":
            self._footer_button.append(btn)

    def build_menu(self, b_cols=1, h_cols=8, f_cols=8):
        menu = [
            self._button[i : i + b_cols] for i in range(0, len(self._button), b_cols)
        ]
        if self._header_button:
            h_cnt = len(self._header_button)
            if h_cnt > h_cols:
                header_buttons = [
                    self._header_button[i : i + h_cols]
                    for i in range(0, len(self._header_button), h_cols)
                ]
                menu = header_buttons + menu
            else:
                menu.insert(0, self._header_button)
        if self._footer_button:
            if len(self._footer_button) > f_cols:
                [
                    menu.append(self._footer_button[i : i + f_cols])
                    for i in range(0, len(self._footer_button), f_cols)
                ]
            else:
                menu.append(self._footer_button)
        return InlineKeyboardMarkup(menu)

    def reset(self):
        self._button = []
        self._header_button = []
        self._footer_button = []
