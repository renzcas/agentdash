import plotly.graph_objs as go

def attractor_panel(trace):
    if len(trace) < 2:
        return go.Figure()

    x_vals, y_vals, z_vals = zip(*trace[-500:])  # last 500 points

    fig = go.Figure(data=[go.Scatter3d(
        x=x_vals, y=y_vals, z=z_vals,
        mode='lines',
        line=dict(color='cyan', width=2)
    )])

    fig.update_layout(
        margin=dict(l=0, r=0, b=0, t=0),
        scene=dict(
            xaxis_title='X',
            yaxis_title='Y',
            zaxis_title='Z'
        )
    )

    return fig