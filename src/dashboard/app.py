import dash
import dash_bootstrap_components as dbc

from callbacks import register_callbacks
from layout import create_layout

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.FLATLY],
    suppress_callback_exceptions=True,
    title="Supply Chain Delivery Risk DSS"
)

server = app.server
app.layout = create_layout()

register_callbacks(app)

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=8050)