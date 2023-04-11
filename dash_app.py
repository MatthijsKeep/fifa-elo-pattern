import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from flask import Flask
import elo

external_stylesheets = [dbc.themes.BOOTSTRAP]

server = Flask(__name__)
app = dash.Dash(__name__, server=server, external_stylesheets=external_stylesheets)

app.layout = dbc.Container(
    [
        html.H1("FIFA Elo Score Calculator"),
        dbc.Row([
            dbc.Col([
                dbc.FormGroup([
                    dbc.Label("Player 1 Elo"),
                    dbc.Input(id="player1-elo", type="number", placeholder="Enter Player 1 Elo"),
                ]),
                dbc.FormGroup([
                    dbc.Label("Player 2 Elo"),
                    dbc.Input(id="player2-elo", type="number", placeholder="Enter Player 2 Elo"),
                ]),
                dbc.FormGroup([
                    dbc.Label("Player 1 Result (0 = loss, 0.5 = draw, 1 = win)"),
                    dbc.Input(id="player1-result", type="number", placeholder="Enter Player 1 Result"),
                ]),
                dbc.Button("Calculate", id="calculate-button", color="primary"),
            ]),
            dbc.Col([
                html.H2("Results"),
                dbc.Alert(id="results", color="info"),
            ]),
        ]),
    ],
    fluid=True
)

@app.callback(
    Output("results", "children"),
    [Input("calculate-button", "n_clicks")],
    [
        State("player1-elo", "value"),
        State("player2-elo", "value"),
        State("player1-result", "value"),
    ],
)
def update_results(n_clicks, player1_elo, player2_elo, player1_result):
    if n_clicks is None or not player1_elo or not player2_elo or player1_result is None:
        return "Please enter all values to calculate updated Elo scores."

    new_elo1, new_elo2 = elo.update_elo(player1_elo, player2_elo, player1_result)

    return f"Player 1 New Elo: {new_elo1:.2f}, Player 2 New Elo: {new_elo2:.2f}"

if __name__ == "__main__":
    app.run_server(debug=True)
