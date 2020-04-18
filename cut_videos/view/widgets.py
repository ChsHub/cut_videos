from wx import ComboBox, CB_DROPDOWN, CB_READONLY, EVT_TEXT, Panel, StaticText, BoxSizer, VERTICAL, Font, EXPAND, HORIZONTAL, \
    NORMAL, MODERN, TextCtrl


class StandardSelection(Panel):
    def __init__(self, parent, callback, title, options):
        super().__init__(parent)

        sizer = BoxSizer(VERTICAL)
        text = StaticText(self, label=title)
        sizer.Add(text)
        self.selection = ComboBox(self, style=CB_DROPDOWN | CB_READONLY, choices=options)
        font = Font(20, MODERN, NORMAL, NORMAL, False, u'Consolas')
        text.SetFont(font)
        self.selection.SetFont(font)
        # self.selection.SetFont(font)
        self.selection.SetValue(options[0])
        if callback:
            self.selection.Bind(EVT_TEXT, lambda x: callback(self.selection.GetValue()))
        sizer.Add(self.selection, 1, EXPAND)
        self.SetSizer(sizer)

    def get_selection(self):
        return self.selection.GetValue()


class SimpleInput(Panel):

    def __init__(self, parent, label, initial=""):
        super().__init__(parent)

        sizer = BoxSizer(HORIZONTAL)
        self._text_input = TextCtrl(self)
        self._text_input.SetFont(Font(40, MODERN, NORMAL, NORMAL, False, u'Consolas'))
        self._text_input.SetValue(initial)
        sizer.Add(self._text_input, 1, EXPAND)

        text = StaticText(self, label=label)
        text.SetFont(Font(20, MODERN, NORMAL, NORMAL, False, u'Consolas'))
        sizer.Add(text, 1, EXPAND)
        self.SetSizer(sizer)

    def get_value(self):
        return self._text_input.GetValue()
