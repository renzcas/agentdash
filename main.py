from dashboards.dashboard import attractor_panel
from modules.chaotic_attention import ChaoticAttention
import numpy as np
from dash import Dash, dcc, html
from dash.dependencies import Input, Output

chaos = ChaoticAttention()

app = Dash(__name__)
app.layout = html.Div([
    html.H2("Lorenz Attractor: Recursive Cognition"),
    dcc.Graph(id='attractor-plot', figure=attractor_panel(chaos.trace)),
    dcc.Interval(id='update-interval', interval=500, n_intervals=0)
])

@app.callback(
    Output('attractor-plot', 'figure'),
    Input('update-interval', 'n_intervals')
)
def update_trace(n):
    chaos.score(np.array([1, 0, 0]), np.array([0, 1, 0]))
    return attractor_panel(chaos.trace)

if __name__ == '__main__':
    app.run(debug=True)