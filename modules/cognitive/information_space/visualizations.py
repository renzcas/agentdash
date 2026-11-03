"""Plotly visualizations for information ecology snapshots."""

from __future__ import annotations

import plotly.graph_objects as go

from .engine import EcologySnapshot


def build_ecology_figure(snapshot: EcologySnapshot) -> go.Figure:
    """Build a radar chart of the snapshot's 11 bounded metrics."""
    dimensions = list(snapshot.scores)
    values = list(snapshot.scores.values())
    return go.Figure(
        data=[
            go.Scatterpolar(
                r=values + values[:1],
                theta=dimensions + dimensions[:1],
                fill="toself",
                name="Information ecology",
            )
        ],
        layout=go.Layout(
            title=f"Information Ecology ({snapshot.signal_count} signals)",
            polar={"radialaxis": {"visible": True, "range": [0, 1]}},
            showlegend=False,
        ),
    )
