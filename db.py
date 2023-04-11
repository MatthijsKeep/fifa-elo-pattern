# db.py

import sqlite3
from sqlite3 import Error
import pandas as pd

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
