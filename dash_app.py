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
from db import create_connection, create_tables, insert_player, update_player, delete_player, get_all_players, get_game_history, add_game_result


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

def update_elo(rating1, rating2, k, score1):
    e1 = 1 / (1 + 10 ** ((rating2 - rating1) / 400))
    e2 = 1 / (1 + 10 ** ((rating1 - rating2) / 400))
    
    new_rating1 = rating1 + k * (score1 - e1)
    new_rating2 = rating2 + k * ((1 - score1) - e2)
    
    return new_rating1, new_rating2

@app.callback(
    Output("remove_player_dropdown", "options"),
    Output("player1_dropdown", "options"),
    Output("player2_dropdown", "options"),
    Output("leaderboard", "data"),
    Input("add_btn", "n_clicks"),
    Input("remove_btn", "n_clicks"),
    Input("submit_result_btn", "n_clicks"),
    State("add_name", "value"),
    State("add_elo", "value"),
    State("remove_player_dropdown", "value"),
    State("player1_dropdown", "value"),
    State("player2_dropdown", "value"),
    State("game_result", "value")
)
def update_leaderboard_and_add_player(
    add_n_clicks, remove_n_clicks, submit_n_clicks,
    name, elo,
    remove_player_value, player1_value, player2_value, game_result_value
):
    global data
    conn = create_connection()
    changed_id = [p["prop_id"] for p in dash.callback_context.triggered][0]

    if "add_btn" in changed_id and name and elo:
        insert_player(conn, (name, float(elo), 0, 0, 0))

    if "remove_btn" in changed_id and remove_player_value:
        delete_player(conn, remove_player_value)

    if "submit_result_btn" in changed_id and player1_value and player2_value and game_result_value:
        add_game_result(conn, player1_value, player2_value, game_result_value)
        print(game_result_value)
        if game_result_value == "p1_wins":
            game_result_value = 1
        elif game_result_value == "p2_wins":
            game_result_value = 0
        else:
            ValueError("Invalid game result value")
        # read in the current elo values
        player1_elo = data.loc[data["name"] == player1_value, "elo"].values[0]
        player2_elo = data.loc[data["name"] == player2_value, "elo"].values[0]
        K = 32
        # Update the player's elo
        player1_elo, player2_elo = update_elo(player1_elo, player2_elo, K, game_result_value)
        # round both elo to integers
        player1_elo = int(round(player1_elo))
        player2_elo = int(round(player2_elo))
        # read in the other player attributes like games, wins, losses
        print(data)
        player1_games = data.loc[data["name"] == player1_value, "games_played"].values[0]
        player1_wins = data.loc[data["name"] == player1_value, "wins"].values[0]
        player1_losses = data.loc[data["name"] == player1_value, "losses"].values[0]

        player2_games = data.loc[data["name"] == player2_value, "games_played"].values[0]
        player2_wins = data.loc[data["name"] == player2_value, "wins"].values[0]
        player2_losses = data.loc[data["name"] == player2_value, "losses"].values[0]

        # update the player attributes
        if game_result_value == "p1_wins":
            player1_wins += 1
            player2_losses += 1
        else:
            player1_losses += 1
            player2_wins += 1

        player1_games += 1
        player2_games += 1

        # update the player attributes in the database
        update_player(conn, (player1_elo, player1_games, player1_wins, player1_losses, player1_value))
        update_player(conn, (player2_elo, player2_games, player2_wins, player2_losses, player2_value))
        

    data = get_all_players(conn)
    conn.close()
    
    player_options = [{"label": row["name"], "value": row["name"]} for _, row in data.iterrows()]
    leaderboard_data = data.to_dict("records")
    # sort the leaderboard by elo
    leaderboard_data = sorted(leaderboard_data, key=lambda x: x["elo"], reverse=True)
    return player_options, player_options, player_options, leaderboard_data


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
