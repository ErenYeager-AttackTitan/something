import json
import sqlite3
import os

# Database file paths
JSON_FILE = "data.json"
SQLITE_FILE = "anime.db"

# Ensure JSON file exists
if not os.path.exists(JSON_FILE):
    with open(JSON_FILE, "w") as f:
        json.dump([], f)

# Ensure SQLite database exists
conn = sqlite3.connect(SQLITE_FILE)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS anime (
    id TEXT PRIMARY KEY,
    name TEXT,
    m3u8 TEXT
)
""")
conn.commit()
conn.close()

# Function to add anime to both JSON and SQLite
def add_anime(anime_id, name, m3u8):
    # Add to JSON
    with open(JSON_FILE, "r+") as f:
        data = json.load(f)
        data.append({"id": anime_id, "name": name, "m3u8": m3u8})
        f.seek(0)
        json.dump(data, f, indent=4)

    # Add to SQLite
    conn = sqlite3.connect(SQLITE_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO anime (id, name, m3u8) VALUES (?, ?, ?)", (anime_id, name, m3u8))
    conn.commit()
    conn.close()

# Function to fetch anime from JSON
def fetch_anime_json(query):
    with open(JSON_FILE, "r") as f:
        data = json.load(f)
        for anime in data:
            if anime["id"] == query or anime["name"].lower() == query.lower():
                return anime
    return None

# Function to fetch anime from SQLite
def fetch_anime_sqlite(query):
    conn = sqlite3.connect(SQLITE_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, m3u8 FROM anime WHERE id=? OR LOWER(name)=?", (query, query.lower()))
    result = cursor.fetchone()
    conn.close()
    if result:
        return {"id": result[0], "name": result[1], "m3u8": result[2]}
    return None

# Function to get anime from either database
def get_anime(query):
    anime = fetch_anime_json(query) or fetch_anime_sqlite(query)
    return anime


