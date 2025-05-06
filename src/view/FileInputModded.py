from wx import FileDialog, FD_OPEN, FD_FILE_MUST_EXIST, FD_MULTIPLE, ID_CANCEL

from wxwidgets._input_widget import InputWidget


class FileInputModded(InputWidget):
    """
    Widget for file input
    """

    def __init__(self, parent: object, callback: object, text_button: str, text_title: str,
                 text_open_file: str, file_type: str = "*.*", initial: str = "", reset: bool = False) -> object:
        """
        Build the widget
        :param parent: Parent wx element
        :param callback: Function, that receives the directory and files
        :param text_button: Text is displayed on the "open-button"
        :param text_title:
        :param text_open_file:
        :param file_type: File types that are displayed (pattern *.type1,*.type2), All types by default
        :param initial: Initial path
        :param reset: If true, don't show last opened directory
        """
        super().__init__(parent, callback, text_button, initial, reset)
        self._file_type = file_type
        self._text_title = text_title
        self._text_open_file = text_open_file

    def button_callback(self, event):
        """
        Receive selection event after files are selected, and pass to callback function
        :param event: Event contains directory and files
        :return: None
        """

        with FileDialog(self, self._text_title, "", "",
                        wildcard=self._text_open_file + '(' + self._file_type + ')|' + self._file_type,
                        style=FD_OPEN | FD_FILE_MUST_EXIST | FD_MULTIPLE) as dialog:
            if dialog.ShowModal() == ID_CANCEL:
                return  # the user changed their mind
            self.set_input_files(dialog.Directory, dialog.Filenames)


    def set_input_files(self, path, files):
        if self._reset:
            self._text_input.SetValue("")
        else:
            self._text_input.SetValue(path)
        self._callback(path=path, files=files)
