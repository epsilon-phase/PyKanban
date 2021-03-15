from PySide2.QtWidgets import *
from PySide2.QtCore import QSettings
from typing import *


class OptionWidget(QWidget):
    @staticmethod
    def get_type_widget(t):
        ret = None
        if isinstance(t, tuple):
            kind = t[0]
            t = t[1:]
            if kind == int:
                ret = QSpinBox()
            if len(t) == 2:
                ret.setMaximum(t[1])
                ret.setMinimum(t[0])
        else:
            kind = t
            if t == int:
                ret = QSpinBox()
            elif t == bool:
                ret = QCheckBox()
            elif t == str:
                ret = QLineEdit()
        return ret, kind

    @property
    def value(self):
        if isinstance(self.widget, QCheckBox):
            return self.widget.isChecked()
        if isinstance(self.widget, QLineEdit):
            return self.widget.text()
        if isinstance(self.widget, QSpinBox):
            return self.widget.value()

    def __init__(self, option_path: str, name: str, description: str, t: type, parent: QWidget = None):
        """
        A widget that holds everything necessary to configure a simple option
        :param option_path: The option path that will be set.
        :param name: The displayed name of the setting
        :param description: The visible description of what the option does
        :param t: The type of the widget
        :param parent:
        """
        super(OptionWidget, self).__init__(parent)
        self.widget, self.valuetype = self.get_type_widget(t)
        self.setLayout(QVBoxLayout())

        cont = QWidget()
        cont.setLayout(QHBoxLayout())
        if not isinstance(self.widget, QCheckBox):
            namelabel = QLabel(name)
            namelabel.setBuddy(self.widget)
            cont.layout().addWidget(namelabel)
        else:
            self.widget.setText(name)
        cont.layout().addWidget(self.widget)
        self.layout().addWidget(cont)

        description = QLabel(description)
        description.setWordWrap(True)
        self.layout().addWidget(description)
        self.option_path = option_path
        self.update_from_setting()

    def update_from_setting(self):
        setting = QSettings()
        val = setting.value(self.option_path, None, self.valuetype)
        if isinstance(val, bool):
            self.widget.setChecked(val)
        elif isinstance(val, int):
            self.widget.setValue(val)
        elif isinstance(val, str):
            self.widget.setText(val)

    def apply_setting(self):
        setting = QSettings()
        setting.setValue(self.option_path, self.value)


class OptionDialog(QDialog):
    def __init__(self, parent=None):
        super(OptionDialog, self).__init__(parent)

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(OptionWidget('Recovery/AutoSave', "Enable Autosave",
                                             """
                                             Enable saving your document regularly.
                                             
                                             Autosaves do not overwrite the original file, so you will be asked whether you want to load from it or not
                                             """, bool))
        self.layout().addWidget(OptionWidget('Recovery/Interval', 'Autosave Interval',
                                             "How many seconds between saves.", (int, 30, 10000)))
        accept_button = QPushButton(self.tr("&Accept"))
        accept_button.clicked.connect(self.update_settings)
        accept_button.clicked.connect(self.accept)
        reject_button = QPushButton(self.tr("&Reject"))
        reject_button.clicked.connect(self.reject)
        hbox = QHBoxLayout()
        hbox.addWidget(accept_button)
        hbox.addWidget(reject_button)
        self.layout().addLayout(hbox)

    def update_settings(self):
        for i in self.findChildren(OptionWidget):
            i.apply_setting()
