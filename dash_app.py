import dash
import dash_auth

import logging
import sqlite3

import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px

from dash import dash_table, html, dcc
from dash.dependencies import Input, Output, State
from datetime import datetime

logging.basicConfig(level=logging.INFO)

# Import the required functions from db.py
from db import create_connection, create_tables, insert_player, update_player, delete_player, get_all_players, get_game_history


# Create a connection to the database and create the table if it doesn't exist
conn = create_connection()
database_name = 'leaderboard.db'
create_tables(conn)

# Replace your existing data variable with data from the database
data = get_all_players(conn)

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.ZEPHYR])
server = app.server

app.layout = html.Div([
    # Add player section
    html.Div([
        html.H3("Add Player"),
        dcc.Input(id="add_name", placeholder="Name"),
        dcc.Input(id="add_elo", placeholder="Elo", type="number"),
        dbc.Button("Add Player", id="add_btn"),
    ]),

    html.Br(),

    # Remove player section
    html.Div([
        html.H3("Remove Player"),
        dcc.Dropdown(id="remove_player_dropdown", options=[]),
        dbc.Button("Remove Player", id="remove_btn"),
    ]),

    html.Br(),

    # Enter game results section
    html.Div([
        html.H3("Enter Game Result"),
        dcc.Dropdown(id="player1_dropdown", options=[]),
        dcc.Dropdown(id="player2_dropdown", options=[]),
        dcc.RadioItems(id="game_result", options=[
            {"label": "Player 1 Wins", "value": "p1_wins"},
            {"label": "Player 2 Wins", "value": "p2_wins"},
        ]),
        dbc.Button("Submit Result", id="submit_result_btn"),
    ]),

    html.Br(),

    # Leaderboard section
    html.Div([
        html.H3("Leaderboard"),
        dash_table.DataTable(
            id="leaderboard",
            columns=[{"name": col, "id": col} for col in data.columns],
            data=data.to_dict("records"),
        ),
    ]),
    
    # add some space between the sections
    html.Br(),

    html.H3("Game History"),

    dbc.Row([
        dbc.Col([
            dbc.Button("Update Game History", id="update_game_history_btn", className="mb-2")
        ])
    ]),

    html.Br(),

    dbc.Row([
        dbc.Col([
            dash_table.DataTable(
                id="game_history_table",
                columns=[
                    {"name": "ID", "id": "id"},
                    {"name": "Timestamp", "id": "timestamp"},
                    {"name": "Player 1", "id": "player1"},
                    {"name": "Player 2", "id": "player2"},
                    {"name": "Winner", "id": "winner"}
                ],
                data=[]
            )
        ])
    ]),
])

@app.callback(
    Output("remove_player_dropdown", "options"),
    Output("player1_dropdown", "options"),
    Output("player2_dropdown", "options"),
    Input("add_btn", "n_clicks"),
    State("add_name", "value"),
    State("add_elo", "value")
)
def add_player(n_clicks, name, elo):
# Replace the data manipulation lines in your add_player callback
    if n_clicks and name and elo:
        global data
        conn = create_connection()
        insert_player(conn, (name, float(elo), 0, 0, 0))
        data = get_all_players(conn)
        conn.close()
    player_options = [{"label": row["name"], "value": row["name"]} for _, row in data.iterrows()]
    return player_options, player_options, player_options


def update_elo(rating1, rating2, k, score1):
    e1 = 1 / (1 + 10 ** ((rating2 - rating1) / 400))
    e2 = 1 / (1 + 10 ** ((rating1 - rating2) / 400))
    
    new_rating1 = rating1 + k * (score1 - e1)
    new_rating2 = rating2 + k * ((1 - score1) - e2)
    
    return new_rating1, new_rating2

@app.callback(
    Output("leaderboard", "data"),
    Input("remove_btn", "n_clicks"),
    Input("submit_result_btn", "n_clicks"),
    State("remove_player_dropdown", "value"),
    State("player1_dropdown", "value"),
    State("player2_dropdown", "value"),
    State("game_result", "value")
)
def update_leaderboard(remove_n_clicks, submit_result_n_clicks, remove_value, player1, player2, game_result):
    global data

    ctx = dash.callback_context
    if not ctx.triggered:
        return data.to_dict("records")

    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if triggered_id == "remove_btn" and remove_value:
        conn = create_connection()
        delete_player(conn, remove_value)
        data = get_all_players(conn)
        conn.close()

    if triggered_id == "submit_result_btn" and player1 and player2 and game_result:
        conn = create_connection()

        player1_elo = data.loc[data["name"] == player1, "elo"].values[0]
        player2_elo = data.loc[data["name"] == player2, "elo"].values[0]

        p1_games_played = data.loc[data["name"] == player1, "games_played"].values[0]
        p2_games_played = data.loc[data["name"] == player2, "games_played"].values[0]

        p1_wins = data.loc[data["name"] == player1, "wins"].values[0]
        p1_losses = data.loc[data["name"] == player1, "losses"].values[0]

        p2_wins = data.loc[data["name"] == player2, "wins"].values[0]
        p2_losses = data.loc[data["name"] == player2, "losses"].values[0]

        k = 32
        if game_result == "p1_wins":
            new_elo1, new_elo2 = update_elo(player1_elo, player2_elo, k, 1)
        else:
            new_elo1, new_elo2 = update_elo(player1_elo, player2_elo, k, 0)

        # Increment the appropriate values
        p1_games_played += 1
        p2_games_played += 1

        if game_result == "p1_wins":
            p1_wins += 1
            p2_losses += 1
            # winner is the name of player1 from data
            winner = data.loc[data["name"] == player1, "name"].values[0]
        else:
            p1_losses += 1
            p2_wins += 1
            winner = data.loc[data["name"] == player2, "name"].values[0]


        # Update player records in the database
        update_player(conn, (int(new_elo1), int(p1_games_played), int(p1_wins), int(p1_losses), player1))
        update_player(conn, (int(new_elo2), int(p2_games_played), int(p2_wins), int(p2_losses), player2))

        # Fetch updated data from the database
        data = get_all_players(conn)

        print("Submitting game result:", player1, player2, winner)
        with sqlite3.connect("leaderboard.db") as conn:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor = conn.cursor()
            cursor.execute("INSERT INTO game_history (timestamp, player1, player2, winner) VALUES (?, ?, ?, ?)",
                        (current_time, player1, player2, winner))
            conn.commit()

            # Debug: print the number of rows affected
            print("Inserted game history, rows affected:", conn.total_changes)
        conn.close()

        data = data.sort_values(by="elo", ascending=False).reset_index(drop=True)

    return data.to_dict("records")

@app.callback(
    Output("game_history_table", "data"),
    Input("update_game_history_btn", "n_clicks")
)
def update_game_history_table(n_clicks):
    # Check if the button has been clicked at least once

    # Query the game_history table to fetch the last 10 games
    with sqlite3.connect("leaderboard.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM game_history ORDER BY timestamp DESC LIMIT 10")
        game_history = cursor.fetchall()
        

    # Convert the results to a list of dictionaries and return it
    return [
        {"id": row[0], "timestamp": row[1], "player1": row[2], "player2": row[3], "winner": row[4]}
        for row in game_history
    ]



VALID_USERNAME_PASSWORD_PAIRS = {
    'sportsco': 'bestco'
}

# Initialize authentication with your app
auth = dash_auth.BasicAuth(
    app,
    VALID_USERNAME_PASSWORD_PAIRS
)

if __name__ == "__main__":
    app.run_server(debug=True)
