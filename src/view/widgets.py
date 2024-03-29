from logging import info

from wx import ComboBox, CB_DROPDOWN, CB_READONLY, EVT_TEXT, Panel, StaticText, BoxSizer, VERTICAL, Font, EXPAND, \
    HORIZONTAL, NORMAL, MODERN, TextCtrl, CENTER
from wxwidgets import SimpleSizer, SimpleButton

from src.resources.gui_texts import window_font, text_color, h1_font


class StandardSelection(Panel):
    def __init__(self, parent, callback, title, options, font):
        super().__init__(parent)

        with SimpleSizer(self, VERTICAL) as sizer:
            text = StaticText(self, label=title)
            text.SetFont(font)
            sizer.Add(text)
            # DROPDOWN
            self.selection = ComboBox(self, style=CB_DROPDOWN | CB_READONLY, choices=options)
            self.selection.SetFont(font)
            self.selection.SetForegroundColour(text_color)
            self.selection.SetOwnForegroundColour(text_color)
            self.selection.SetValue(options[0])
            if callback:
                self.selection.Bind(EVT_TEXT, lambda x: callback(self.selection.GetValue()))
            sizer.Add(self.selection, 1, EXPAND)

    def get_selection(self):
        return self.selection.GetValue()


class SimpleInput(Panel):

    def __init__(self, parent, label, initial=""):
        super().__init__(parent)

        sizer = BoxSizer(HORIZONTAL)
        self._text_input = TextCtrl(self)
        self._text_input.SetFont(h1_font)
        self._text_input.SetValue(initial)
        sizer.Add(self._text_input, 1, EXPAND)

        text = StaticText(self, label=label)
        text.SetFont(h1_font)
        sizer.Add(text, 1, EXPAND)
        self.SetSizer(sizer)

    def get_value(self):
        return self._text_input.GetValue()


class DigitInput(Panel):
    def __init__(self, parent):
        super().__init__(parent)
        self.mod = 10
        self.digit = 0

        with SimpleSizer(self, VERTICAL) as sizer:
            button = SimpleButton(self, text_button='+', callback=self._plus, size=(40, 10))
            sizer.Add(button, 1)

            self._text_input = TextCtrl(self, size=(40, 70))
            self._text_input.SetFont(Font(40, MODERN, NORMAL, NORMAL, False, u'Consolas'))
            self._text_input.SetValue('0')
            sizer.Add(self._text_input, 0)

            sizer.Add(SimpleButton(self, text_button='-', callback=self._minus, size=(40, 20)), 1)

    def _plus(self, _):
        self.digit += 1
        self.digit %= self.mod
        self._text_input.SetValue(str(self.digit))

    def _minus(self, _):
        self.digit -= 1
        self.digit %= self.mod
        self._text_input.SetValue(str(self.digit))

    def get_value(self):
        return self._text_input.GetValue()

    def set_value(self, digit: str):
        self.digit = int(digit)
        self._text_input.SetValue(str(self.digit))


class TimeInput(Panel):
    def __init__(self, parent, label, initial='00:00:00.0'):
        super().__init__(parent)

        self._digits = []
        with SimpleSizer(self, HORIZONTAL) as sizer:
            # Add time elements
            for s in list('dd:dd:dd.ddd') + [label]:
                if s == 'd':
                    self._digits.append(DigitInput(self))
                    sizer.Add(self._digits[-1], proportion=0, flag=CENTER)
                else:
                    text = StaticText(self, label=s)
                    text.SetFont(h1_font)
                    sizer.Add(text, proportion=0, flag=CENTER)

        # Set modulo for leading digits of seconds and minutes
        self._digits[2].mod = 6
        self._digits[4].mod = 6

    def get_value(self):
        digits = list(map(lambda x: x.get_value(), self._digits))
        digits = ''.join(digits)
        digits = digits[:2] + ':' + digits[2:4] + ':' + digits[4:6] + '.' + digits[6:]
        info(f"Digits: {digits}")
        return digits

    def set_value(self, digits: str):
        if not len(self._digits) == len(digits):
            raise ValueError
        for digit_input, digit in zip(self._digits, digits):
            digit_input.set_value(digit)
