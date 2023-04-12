import dash
import dash_auth

import logging
import sqlite3

import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px

from dash import dash_table, html, dcc
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from datetime import datetime

logging.basicConfig(level=logging.INFO)

# Import the required functions from db.py
from db import create_connection, create_tables, insert_player, update_player, delete_player, get_all_players,\
               get_game_history, add_game_result, get_table, get_columns, update_row_in_db, delete_row_from_db


# Create a connection to the database and create the table if it doesn't exist
conn = create_connection()
database_name = 'leaderboard.db'
create_tables(conn)

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.ZEPHYR])
server = app.server

# Functions to fetch data from the databases, edit, insert, and delete rows.
# Please provide the existing functions or create new ones as needed.

# Layout
app.layout = html.Div([
    html.H1("Admin Dashboard"),
    dcc.Link("Go to Main App", href="/"),

    dcc.Dropdown(
        id="database_dropdown",
        options=[
            {"label": "leaderboard", "value": "leaderboard.db"},
        ],
        placeholder="Select a database"
    ),

    dcc.Dropdown(
        id="table_dropdown",
        options=[],
        placeholder="Select a table"
    ),

    html.Button("View Table", id="view_table_btn"),
    html.Button("Insert", id="insert_btn"),
    html.Button("Edit", id="submit_update_btn"),
    html.Button("Delete", id="submit_delete_btn"),

    dcc.Input(id="row_id", placeholder="Row ID", type="number"),
    dcc.Input(id="column_name", placeholder="Column Name"),
    dcc.Input(id="new_value", placeholder="New Value"),

    html.Div(id="table_change_output"),

    dash_table.DataTable(
    id="table_view",
    style_table={"overflowX": "auto"},
    editable=True,
    row_deletable=True,
    ),

])

# Callbacks and other logic here
# You'll need to create callbacks to handle user interactions, update the UI elements, and execute the database functions.


# Callback to load in the database names 

@app.callback(
    Output("table_dropdown", "options"),
    Input("database_dropdown", "value")
)

def update_table_options(database_name):
    if not database_name:
        print("No database selected")
        return []
        
    tables = get_table(database_name)
    return [{"label": table, "value": table} for table in tables]

# Callback to view the tables

@app.callback(
    Output("table_view", "data"),
    Output("table_view", "columns"),
    Input("database_dropdown", "value"),
    Input("table_dropdown", "value")
)
def view_table(database_name, table_name):
    if not database_name or not table_name:
        return [], []

    conn = create_connection(database_name)
    df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
    conn.close()

    columns = [{"name": col, "id": col} for col in df.columns]
    data = df.to_dict("records")

    return data, columns

@app.callback(
    Output("table_change_output", "children"),
    Input("submit_update_btn", "n_clicks"),
    Input("submit_delete_btn", "n_clicks"),
    State("database_dropdown", "value"),
    State("table_dropdown", "value"),
    State("row_id", "value"),
    State("column_name", "value"),
    State("new_value", "value"),
)
def handle_table_changes(n_clicks_update, n_clicks_delete, database_name, table_name, row_id, column_name, new_value):
    ctx = dash.callback_context
    if not ctx.triggered or not table_name or row_id is None:
        return ""

    button_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if button_id == "submit_update_btn":
        print(table_name, row_id, column_name, new_value)
        update_row_in_db(database_name, table_name, row_id, column_name, new_value)
        return f"Updated row with ID {row_id} in the {table_name} table. Set {column_name} to {new_value}."
    elif button_id == "submit_delete_btn":
        print(database_name, table_name, row_id)
        delete_row_from_db(database_name, table_name, row_id)
        return f"Deleted row with ID {row_id} from the {table_name} table."
    else:
        return ""



if __name__ == "__main__":
    app.run_server(debug=True,  host='0.0.0.0')

