"""Shared qualitative palettes and narrow color updates for time-series presentation."""

from dataclasses import replace

from .style_schema import normalize_color


DISTINCT_TIME_SERIES_COLORS = (
    # Saturated / primary tab10 group first.
    "#1f77b4",  # blue
    "#ff7f0e",  # orange
    "#2ca02c",  # green
    "#d62728",  # red
    "#9467bd",  # purple
    "#8c564b",  # brown
    "#e377c2",  # pink
    "#7f7f7f",  # gray
    "#bcbd22",  # olive
    "#17becf",  # cyan

    # Lighter tab20 companions second.
    "#aec7e8",  # light blue
    "#ffbb78",  # light orange
    "#98df8a",  # light green
    "#ff9896",  # light red
    "#c5b0d5",  # light purple
    "#c49c94",  # light brown
    "#f7b6d2",  # light pink
    "#c7c7c7",  # light gray
    "#dbdb8d",  # light olive
    "#9edae5",  # light cyan
)


def with_series_family_color(presentation, color):
    """Return ``presentation`` with only Series/Ensemble identity colors changed."""
    normalized = normalize_color(color, DISTINCT_TIME_SERIES_COLORS[0])
    series = replace(
        presentation.series,
        marker_color=normalized,
        line_color=normalized,
    )
    ensemble = replace(
        presentation.ensemble,
        member_line_color=normalized,
        fill_color=normalized,
    )
    return replace(presentation, series=series, ensemble=ensemble)


def _color_key(value):
    """Return a stable comparison key for serialized Series colors."""
    return normalize_color(value, "").strip().lower()


def distinct_palette_usage(records, palette=DISTINCT_TIME_SERIES_COLORS):
    """Return per-palette-color committed-record usage from primary Series colors."""
    normalized_palette = tuple(_color_key(color) for color in palette)
    counts = [0] * len(normalized_palette)
    index_by_color = {color: index for index, color in enumerate(normalized_palette)}
    for record in records:
        series = record.presentation.series
        used_by_record = {
            _color_key(series.marker_color),
            _color_key(series.line_color),
        }
        for color in used_by_record:
            index = index_by_color.get(color)
            if index is not None:
                counts[index] += 1
    return tuple(counts)


def allocate_distinct_series_color(records, palette=DISTINCT_TIME_SERIES_COLORS):
    """Choose the first unused palette color, then least-used with palette-order ties."""
    palette = tuple(palette)
    if not palette:
        raise ValueError("distinct color palette must not be empty")
    counts = distinct_palette_usage(records, palette)
    for index, count in enumerate(counts):
        if count == 0:
            return palette[index]
    minimum = min(counts)
    return palette[next(index for index, count in enumerate(counts) if count == minimum)]


def apply_auto_color_to_new_series(
    presentation, committed_records, *, enabled, palette=DISTINCT_TIME_SERIES_COLORS
):
    """Apply the creation policy after normal defaults have produced a presentation."""
    if not enabled:
        return presentation
    color = allocate_distinct_series_color(committed_records, palette)
    return with_series_family_color(presentation, color)


def assign_distinct_family_colors(records, palette=DISTINCT_TIME_SERIES_COLORS):
    """Return records recolored deterministically in palette order for batch commands."""
    palette = tuple(palette)
    if not palette:
        raise ValueError("distinct color palette must not be empty")
    return tuple(
        replace(
            record,
            presentation=with_series_family_color(
                record.presentation, palette[index % len(palette)]
            ),
        )
        for index, record in enumerate(records)
    )
