# db.py

import sqlite3
from sqlite3 import Error
import pandas as pd
from datetime import datetime

def create_connection(db_file="leaderboard.db"):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Error as e:
        print(e)

    return conn

def create_tables(conn):
    try:
        cursor = conn.cursor()
        cursor.execute("""CREATE TABLE IF NOT EXISTS leaderboard (
                            id INTEGER PRIMARY KEY,
                            name TEXT NOT NULL,
                            elo REAL NOT NULL,
                            games_played INTEGER NOT NULL,
                            wins INTEGER NOT NULL,
                            losses INTEGER NOT NULL
                        );""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS game_history (
                            id INTEGER PRIMARY KEY,
                            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                            player1 TEXT NOT NULL,
                            player2 TEXT NOT NULL,
                            winner TEXT NOT NULL
                        );""")
    except Error as e:
        print(e)

def insert_player(conn, player):
    sql = """INSERT INTO leaderboard(name, elo, games_played, wins, losses)
             VALUES(?,?,?,?,?)"""
    cursor = conn.cursor()
    cursor.execute(sql, player)
    conn.commit()
    return cursor.lastrowid

def update_player(conn, player_data):
    sql = '''
        UPDATE leaderboard
        SET elo = ?,
            games_played = ?,
            wins = ?,
            losses = ?
        WHERE name = ?
    '''
    cur = conn.cursor()
    cur.execute(sql, player_data)
    conn.commit()




def delete_player(conn, name):
    sql = "DELETE FROM leaderboard WHERE name=?"
    cursor = conn.cursor()
    cursor.execute(sql, (name,))
    conn.commit()

def get_all_players(conn):
    sql = "SELECT id, name, elo, CAST(games_played AS INTEGER) AS games_played, CAST(wins AS INTEGER) AS wins, CAST(losses AS INTEGER) AS losses FROM leaderboard"
    df = pd.read_sql_query(sql, conn)
    return df

def get_game_history(conn):
    sql = "SELECT * FROM game_history"
    df = pd.read_sql_query(sql, conn)
    return df

def add_game_result(conn, player1, player2, winner):
    print("Submitting game result:", player1, player2, winner)
    if winner == "p2_wins":
        winner = player2
    elif winner == "p1_wins":
        winner = player1

    # Insert game history data
    with sqlite3.connect("leaderboard.db") as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO game_history (timestamp, player1, player2, winner) VALUES (?, ?, ?, ?)",
                       (datetime.now(), player1, player2, winner))
        conn.commit()

        # Debug: print the number of rows affected
        print("Inserted game history, rows affected:", conn.total_changes)

def get_table(database_name):
    conn = sqlite3.connect(database_name)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    conn.close()
    return [table[0] for table in tables]

def get_columns(database_name, table_name):
    conn = sqlite3.connect(database_name)
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    column_names = [column_info[1] for column_info in cursor.fetchall()]
    conn.close()
    return column_names

def update_row_in_db(database_name, table_name, row_id, column_name, new_value):
    conn = sqlite3.connect(database_name)
    cursor = conn.cursor()
    cursor.execute(f"UPDATE {table_name} SET {column_name} = ? WHERE id = ?", (new_value, row_id))
    conn.commit()
    conn.close()

def delete_row_from_db(database_name, table_name, row_id):
    conn = sqlite3.connect(database_name)
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM {table_name} WHERE id = ?", (row_id,))
    conn.commit()
    conn.close()