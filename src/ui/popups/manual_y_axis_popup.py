"""Transactional four-domain Manual Y-axis editor."""

import math

from qgis.PyQt.QtCore import pyqtSignal
from qgis.PyQt.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ...qt_compat import (
    FRAME_SHAPE_STYLED_PANEL,
    POPUP_WINDOW_FLAG,
    SIZE_POLICY_FIXED,
)
from ...time_series.y_axis_range import resolve_manual_y_range
from ..spacing import SPACE_LG, SPACE_MD, SPACE_SM, SPACE_XL


class ManualYAxisPopup(QFrame):
    """Edit four independent Y domains without mutating authoritative state on open."""

    previewChanged = pyqtSignal(str, object, object)
    applyRequested = pyqtSignal(object)
    cancelRequested = pyqtSignal()
    currentViewRequested = pyqtSignal(str)

    DOMAINS = (
        "series",
        "right_series",
        "residual",
        "right_residual",
    )
    PLOT_TABS = (
        ("Main", ("series", "right_series")),
        ("Residual", ("residual", "right_residual")),
    )
    AXIS_SECTION_TITLES = {
        "series": "Left axis",
        "right_series": "Right axis",
        "residual": "Left axis",
        "right_residual": "Right axis",
    }

    def __init__(self, parent=None):
        """Create Main/Residual tabs containing the four independent axis editors."""
        super().__init__(parent, POPUP_WINDOW_FLAG)
        self.setObjectName("popup_manual_y_axis")
        self.setFrameShape(FRAME_SHAPE_STYLED_PANEL)
        self._closing_after_apply = False
        self._loading = False
        self._editors = {}
        self._control_axes = {}
        self._changed = {name: False for name in self.DOMAINS}
        self._captured_exact = {name: None for name in self.DOMAINS}
        self._data_bounds = {name: None for name in self.DOMAINS}
        self._available = {name: False for name in self.DOMAINS}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACE_XL, SPACE_LG, SPACE_XL, SPACE_LG)
        layout.setSpacing(SPACE_MD)

        title = QLabel("Manual Y-axis", self)
        title.setObjectName("label_manual_y_axis_title")
        layout.addWidget(title)

        self.tabs = QTabWidget(self)
        self.tabs.setObjectName("tabs_manual_y_axis")
        self._plot_pages = {}
        self._axis_sections = {}
        for plot_name, domains in self.PLOT_TABS:
            page = QWidget(self.tabs)
            page.setObjectName(f"page_manual_y_axis_{plot_name.lower()}")
            page.setAccessibleName(f"{plot_name} Y axes")
            page_layout = QVBoxLayout(page)
            page_layout.setContentsMargins(SPACE_SM, SPACE_MD, SPACE_SM, SPACE_SM)
            page_layout.setSpacing(SPACE_MD)
            for domain in domains:
                page_layout.addWidget(self._createAxisSection(domain, page))
            page_layout.addStretch(1)
            self._plot_pages[plot_name.lower()] = page
            self.tabs.addTab(page, plot_name)
        layout.addWidget(self.tabs)

        actions = QHBoxLayout()
        actions.addStretch(1)
        self.cancel_button = QPushButton("Cancel", self)
        self.apply_button = QPushButton("Apply", self)
        actions.addWidget(self.cancel_button)
        actions.addWidget(self.apply_button)
        layout.addLayout(actions)

        self.cancel_button.clicked.connect(self.close)
        self.apply_button.clicked.connect(self._apply)

    def _createAxisSection(self, axis_name, parent):
        """Create and register one canonical Y-domain editor section."""
        section = QGroupBox(self.AXIS_SECTION_TITLES[axis_name], parent)
        section.setObjectName(f"group_manual_y_axis_{axis_name}")
        outer = QVBoxLayout(section)
        outer.setContentsMargins(SPACE_MD, SPACE_MD, SPACE_MD, SPACE_SM)

        grid = QGridLayout()
        grid.addWidget(QLabel("Auto", section), 0, 1)
        grid.addWidget(QLabel("Value", section), 0, 2)
        controls = {}

        for row, bound in enumerate(("upper", "lower"), 1):
            auto = QCheckBox("", section)
            value = QDoubleSpinBox(section)
            auto.setAccessibleName(
                f"{axis_name} {bound} automatic Y-axis bound"
            )
            value.setAccessibleName(
                f"{axis_name} {bound} manual Y-axis bound"
            )
            value.setRange(-1e9, 1e9)
            value.setDecimals(1)
            value.setSingleStep(1.0)
            value.setFixedWidth(105)
            value.setSizePolicy(SIZE_POLICY_FIXED, SIZE_POLICY_FIXED)
            auto.toggled.connect(self._editorChanged)
            value.valueChanged.connect(self._editorChanged)
            self._control_axes[auto] = axis_name
            self._control_axes[value] = axis_name
            grid.addWidget(QLabel(bound.title(), section), row, 0)
            grid.addWidget(auto, row, 1)
            grid.addWidget(value, row, 2)
            controls[bound] = (auto, value)

        outer.addLayout(grid)
        button = QPushButton("Use current view", section)
        button.clicked.connect(
            lambda _checked=False, name=axis_name: self.currentViewRequested.emit(name)
        )
        outer.addWidget(button)
        controls["use_current_view"] = button
        self._editors[axis_name] = controls
        self._axis_sections[axis_name] = section
        return section

    def openForDomains(self, manuals, data_bounds, availability):
        """Load drafts for all domains while preserving inactive stored values."""
        self._loading = True
        self._available = dict(availability)
        self._changed = {name: False for name in self.DOMAINS}
        self._captured_exact = {name: None for name in self.DOMAINS}
        self._data_bounds = dict(data_bounds)

        for name in self.DOMAINS:
            manual = manuals[name]
            bounds = data_bounds.get(name) or (0.0, 1.0)
            for bound_name, active, retained, seeded in (
                ("lower", manual.lower, manual.retained_lower, bounds[0]),
                ("upper", manual.upper, manual.retained_upper, bounds[1]),
            ):
                auto, value = self._editors[name][bound_name]
                value.setValue(
                    float(retained if retained is not None else seeded)
                )
                auto.setChecked(active is None)
            self._setDomainEnabled(name, bool(availability.get(name, False)))

        self._loading = False
        self._updateState()
        self._closing_after_apply = False

    def _setDomainEnabled(self, name, active):
        """Enable one domain's controls while keeping its tab visible."""
        for bound in ("lower", "upper"):
            auto, value = self._editors[name][bound]
            auto.setEnabled(active)
            value.setEnabled(active and not auto.isChecked())
        self._editors[name]["use_current_view"].setEnabled(active)

    def setCurrentView(self, axis_name, lower, upper):
        """Populate one draft from its current ViewBox without committing settings."""
        if not self._available.get(axis_name, False):
            return

        self._loading = True
        for bound, number in (("lower", lower), ("upper", upper)):
            auto, value = self._editors[axis_name][bound]
            value.setValue(float(number))
            auto.setChecked(False)
        self._loading = False
        self._changed[axis_name] = True
        self._captured_exact[axis_name] = (float(lower), float(upper))
        self._updateState()

    def bounds(self, name):
        """Return the draft lower/upper policy for one domain."""
        captured = self._captured_exact.get(name)
        if captured is not None:
            return captured
        return tuple(
            None if self._editors[name][bound][0].isChecked()
            else float(self._editors[name][bound][1].value())
            for bound in ("lower", "upper")
        )

    def retainedBounds(self, name):
        """Return retained numeric editor values for one domain."""
        captured = self._captured_exact.get(name)
        if captured is not None:
            return captured
        return tuple(
            float(self._editors[name][bound][1].value())
            for bound in ("lower", "upper")
        )

    def _isValid(self, name):
        """Return whether one active domain's draft can resolve to a finite range."""
        if not self._available.get(name, False):
            return True

        lower, upper = self.bounds(name)
        if lower is not None and upper is not None:
            return (
                math.isfinite(lower)
                and math.isfinite(upper)
                and lower < upper
            )

        data = self._data_bounds.get(name)
        return data is not None and resolve_manual_y_range(
            *data, lower, upper
        ) is not None

    def _updateState(self):
        """Refresh value-editor enablement and Apply validity."""
        for name in self.DOMAINS:
            for bound in ("lower", "upper"):
                auto, value = self._editors[name][bound]
                value.setEnabled(auto.isEnabled() and not auto.isChecked())
        self.apply_button.setEnabled(
            all(self._isValid(name) for name in self.DOMAINS)
        )

    def _editorChanged(self, *_args):
        """Track and preview one edited domain without committing settings."""
        if self._loading:
            return
        name = self._control_axes.get(self.sender())
        if name is None:
            return

        self._changed[name] = True
        self._captured_exact[name] = None
        self._updateState()
        if self._isValid(name):
            self.previewChanged.emit(name, *self.bounds(name))

    def _apply(self):
        """Emit changed-domain drafts and close without a Cancel signal."""
        if not self.apply_button.isEnabled():
            return

        payload = {}
        for name in self.DOMAINS:
            payload[name] = {
                "bounds": self.bounds(name),
                "retained": self.retainedBounds(name),
                "changed": self._changed[name],
            }
        self._closing_after_apply = True
        self.applyRequested.emit(payload)
        self.close()

    def closeAfterCommit(self):
        """Close after external completion without emitting Cancel."""
        self._closing_after_apply = True
        self.close()

    def closeEvent(self, event):
        """Treat dismissal and Escape as transaction cancellation."""
        if not self._closing_after_apply:
            self.cancelRequested.emit()
        self._closing_after_apply = False
        super().closeEvent(event)
