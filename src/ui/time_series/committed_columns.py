"""Column schema and geometry for the committed time-series list."""

from enum import IntEnum


class CommittedTimeSeriesColumn(IntEnum):
    """Fixed committed-list column order."""

    COLOR = 0
    VISIBLE = 1
    SEQUENCE = 2
    LABEL = 3
    TARGET = 4
    REFERENCE = 5
    Y_AXIS = 6


COMMITTED_COLUMN_COUNT = len(CommittedTimeSeriesColumn)
COMMITTED_COLOR_COLUMN_WIDTH = 8
COMMITTED_VISIBLE_COLUMN_WIDTH = 24
COMMITTED_SEQUENCE_COLUMN_WIDTH = 28
COMMITTED_Y_AXIS_COLUMN_WIDTH = 24
