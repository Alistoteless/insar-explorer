"""Compact popup for persistent time-series plot appearance."""

from qgis.PyQt.QtCore import pyqtSignal
from qgis.PyQt.QtWidgets import (
    QComboBox, QFormLayout, QGridLayout, QGroupBox, QHBoxLayout, QLabel,
    QLineEdit, QSpinBox, QTabWidget, QVBoxLayout, QWidget,
)

from ...qt_compat import POPUP_WINDOW_FLAG, SIZE_POLICY_FIXED
from ..spacing import SPACE_MD
from .time_series_style_popup import CompactColorButton
from .defaults_menu import createDefaultsMenu


class AppearancePopup(QWidget):
    """Edit all persistent plot presentation settings without Apply or Cancel."""

    settingsChanged = pyqtSignal(
        str, str, str, str, str, str, str, str, str, int, str, str, str
    )
    applySavedTextAxesDefaultRequested = pyqtSignal()
    saveCurrentTextAxesAsDefaultRequested = pyqtSignal()
    applyFactoryTextAxesDefaultRequested = pyqtSignal()
    applySavedPlotStyleDefaultRequested = pyqtSignal()
    saveCurrentPlotStyleAsDefaultRequested = pyqtSignal()
    applyFactoryPlotStyleDefaultRequested = pyqtSignal()

    GRID_MODES = (
        ("Both", "both"),
        ("Horizontal", "horizontal"),
        ("Vertical", "vertical"),
        ("None", "none"),
    )

    DATE_FORMATS = (
        ("YYYY-MM-DD", "%Y-%m-%d"),
        ("DD/MM/YYYY", "%d/%m/%Y"),
        ("MM/DD/YYYY", "%m/%d/%Y"),
        ("DD Mon YYYY", "%d %b %Y"),
        ("Mon YYYY", "%b %Y"),
        ("YYYY", "%Y"),
    )

    def __init__(self, parent=None):
        """Build the two-tab popup with immediate commit semantics."""
        super().__init__(parent, POPUP_WINDOW_FLAG)
        self.setObjectName("appearancePopup")
        self.setWindowTitle("Appearance")

        layout = QVBoxLayout(self)
        self.tabs = QTabWidget(self)
        self.tabs.setObjectName("tabs_appearance")
        self.text_axes_tab = QWidget(self.tabs)
        self.text_axes_tab.setObjectName("tab_appearance_text_axes")
        self.plot_style_tab = QWidget(self.tabs)
        self.plot_style_tab.setObjectName("tab_appearance_plot_style")

        self._buildTextAxesTab()
        self._buildPlotStyleTab()
        self.tabs.addTab(self.text_axes_tab, "Text & axes")
        self.tabs.addTab(self.plot_style_tab, "Plot style")
        layout.addWidget(self.tabs)

        for editor in self._textEditors():
            editor.editingFinished.connect(self._emitSettings)
        self.date_format_combo.currentTextChanged.connect(self._emitSettings)
        self.font_size_spin.valueChanged.connect(self._emitSettings)
        self.grid_mode_combo.currentIndexChanged.connect(self._emitSettings)
        self.plot_background_button.colorChanged.connect(self._emitSettings)
        self.canvas_background_button.colorChanged.connect(self._emitSettings)

    def _buildTextAxesTab(self):
        """Create title, axis-label, and date-format controls."""
        layout = QVBoxLayout(self.text_axes_tab)
        text_group = QGroupBox("Text", self.text_axes_tab)
        text_layout = QGridLayout(text_group)
        text_layout.setHorizontalSpacing(SPACE_MD)
        text_layout.addWidget(QLabel("", text_group), 0, 0)
        text_layout.addWidget(QLabel("Time series", text_group), 0, 1)
        text_layout.addWidget(QLabel("Residual", text_group), 0, 2)

        self.time_series_title_edit = self._compactLineEdit(text_group)
        self.residual_title_edit = self._compactLineEdit(text_group)
        self.time_series_x_label_edit = self._compactLineEdit(text_group)
        self.residual_x_label_edit = self._compactLineEdit(text_group)
        rows = (
            ("Title", self.time_series_title_edit, self.residual_title_edit),
            ("X label", self.time_series_x_label_edit, self.residual_x_label_edit),
        )
        for row, (label, series_edit, residual_edit) in enumerate(rows, start=1):
            text_layout.addWidget(QLabel(label, text_group), row, 0)
            text_layout.addWidget(series_edit, row, 1)
            text_layout.addWidget(residual_edit, row, 2)
        layout.addWidget(text_group)

        self.time_series_y_label_edit = self._compactLineEdit(self.text_axes_tab)
        self.right_y_label_edit = self._compactLineEdit(self.text_axes_tab)
        self.residual_y_label_edit = self._compactLineEdit(self.text_axes_tab)
        self.residual_right_y_label_edit = self._compactLineEdit(self.text_axes_tab)
        y_labels = QGroupBox("Y-axis labels", self.text_axes_tab)
        y_labels_form = QFormLayout(y_labels)
        y_labels_form.addRow("Main left Y", self.time_series_y_label_edit)
        y_labels_form.addRow("Main right Y", self.right_y_label_edit)
        y_labels_form.addRow("Residual left Y", self.residual_y_label_edit)
        y_labels_form.addRow("Residual right Y", self.residual_right_y_label_edit)
        layout.addWidget(y_labels)

        self.date_format_combo = QComboBox(self.text_axes_tab)
        for label, value in self.DATE_FORMATS:
            self.date_format_combo.addItem(label, value)
        self.date_format_combo.setEditable(True)
        self.date_format_combo.setMinimumWidth(150)
        date_formatting = QGroupBox("Formatting", self.text_axes_tab)
        date_formatting_form = QFormLayout(date_formatting)
        date_formatting_form.addRow("Date format", self.date_format_combo)
        layout.addWidget(date_formatting)
        layout.addStretch(1)
        actions = QHBoxLayout()
        actions.addStretch(1)
        self.text_axes_defaults_button = createDefaultsMenu(
            self.text_axes_tab, self.applySavedTextAxesDefaultRequested.emit,
            self.saveCurrentTextAxesAsDefaultRequested.emit,
            self.applyFactoryTextAxesDefaultRequested.emit,
            "button_appearance_text_axes_defaults",
        )
        actions.addWidget(self.text_axes_defaults_button)
        layout.addLayout(actions)

    def _buildPlotStyleTab(self):
        """Create global font, grid, and background appearance controls."""
        layout = QVBoxLayout(self.plot_style_tab)
        self.font_size_spin = QSpinBox(self.plot_style_tab)
        self.font_size_spin.setRange(1, 200)
        self.font_size_spin.setMaximumWidth(80)
        self.grid_mode_combo = QComboBox(self.plot_style_tab)
        self.grid_mode_combo.setEditable(False)
        self.grid_mode_combo.setMaximumWidth(140)
        for label, value in self.GRID_MODES:
            self.grid_mode_combo.addItem(label, value)
        formatting = QGroupBox("Formatting", self.plot_style_tab)
        formatting_form = QFormLayout(formatting)
        formatting_form.addRow("Font size", self.font_size_spin)
        formatting_form.addRow("Grid", self.grid_mode_combo)
        layout.addWidget(formatting)

        self.plot_background_button = CompactColorButton(
            "■", "Select plot area background", self.plot_style_tab
        )
        self.canvas_background_button = CompactColorButton(
            "■", "Select canvas background", self.plot_style_tab
        )
        colors = QGroupBox("Colors", self.plot_style_tab)
        colors_form = QFormLayout(colors)
        colors_form.addRow("Plot area background", self.plot_background_button)
        colors_form.addRow("Canvas background", self.canvas_background_button)
        layout.addWidget(colors)
        layout.addStretch(1)
        actions = QHBoxLayout()
        actions.addStretch(1)
        self.plot_style_defaults_button = createDefaultsMenu(
            self.plot_style_tab, self.applySavedPlotStyleDefaultRequested.emit,
            self.saveCurrentPlotStyleAsDefaultRequested.emit,
            self.applyFactoryPlotStyleDefaultRequested.emit,
            "button_appearance_plot_style_defaults",
        )
        actions.addWidget(self.plot_style_defaults_button)
        layout.addLayout(actions)

    def _compactLineEdit(self, parent=None):
        """Return a width-bounded single-line editor suitable for two columns."""
        editor = QLineEdit(parent or self)
        editor.setFixedWidth(118)
        editor.setSizePolicy(SIZE_POLICY_FIXED, SIZE_POLICY_FIXED)
        return editor

    def _textEditors(self):
        """Return text controls in canonical runtime field order."""
        return (
            self.time_series_title_edit, self.residual_title_edit,
            self.time_series_x_label_edit, self.residual_x_label_edit,
            self.time_series_y_label_edit, self.right_y_label_edit,
            self.residual_y_label_edit, self.residual_right_y_label_edit,
        )

    def settings(self):
        """Return the complete appearance value currently displayed."""
        date_format = self.date_format_combo.currentData()
        known_labels = [
            self.date_format_combo.itemText(i)
            for i in range(self.date_format_combo.count())
        ]
        if self.date_format_combo.isEditable() and self.date_format_combo.currentText() not in known_labels:
            date_format = self.date_format_combo.currentText()
        return (
            self.time_series_title_edit.text(),
            self.residual_title_edit.text(),
            self.time_series_x_label_edit.text(),
            self.residual_x_label_edit.text(),
            self.time_series_y_label_edit.text(),
            self.right_y_label_edit.text(),
            self.residual_y_label_edit.text(),
            self.residual_right_y_label_edit.text(),
            str(date_format or "%Y-%m-%d"),
            int(self.font_size_spin.value()),
            str(self.grid_mode_combo.currentData() or "both"),
            self.plot_background_button.color(),
            self.canvas_background_button.color(),
        )

    def setSettings(self, settings):
        """Refresh every control without emitting persistence writes."""
        widgets = self._textEditors() + (
            self.date_format_combo, self.font_size_spin, self.grid_mode_combo,
            self.plot_background_button, self.canvas_background_button,
        )
        previous = [widget.blockSignals(True) for widget in widgets]
        try:
            self.time_series_title_edit.setText(settings.time_series_title)
            self.residual_title_edit.setText(settings.residual_title)
            self.time_series_x_label_edit.setText(settings.time_series_x_label)
            self.residual_x_label_edit.setText(settings.residual_x_label)
            self.time_series_y_label_edit.setText(settings.time_series_y_label)
            self.right_y_label_edit.setText(settings.right_y_label)
            self.residual_y_label_edit.setText(settings.residual_y_label)
            self.residual_right_y_label_edit.setText(settings.residual_right_y_label)
            index = self.date_format_combo.findData(settings.date_format)
            if index >= 0:
                self.date_format_combo.setCurrentIndex(index)
            else:
                self.date_format_combo.setEditText(settings.date_format or "%Y-%m-%d")
            self.font_size_spin.setValue(int(settings.font_size))
            grid_index = self.grid_mode_combo.findData(settings.grid_mode)
            self.grid_mode_combo.setCurrentIndex(grid_index if grid_index >= 0 else 0)
            self.plot_background_button.setColor(settings.plot_background)
            self.canvas_background_button.setColor(settings.canvas_background)
        finally:
            for widget, blocked in zip(widgets, previous):
                widget.blockSignals(blocked)

    def _emitSettings(self, *_args):
        """Emit one complete immutable replacement after a user edit."""
        self.settingsChanged.emit(*self.settings())
