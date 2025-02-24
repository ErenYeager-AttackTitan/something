import json
import sqlite3
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse

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
    name TEXT
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS episodes (
    anime_id TEXT,
    episode TEXT,
    m3u8 TEXT,
    PRIMARY KEY (anime_id, episode),
    FOREIGN KEY (anime_id) REFERENCES anime(id)
)
""")
conn.commit()
conn.close()

# Function to add anime
def add_anime(anime_id, name):
    conn = sqlite3.connect(SQLITE_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO anime (id, name) VALUES (?, ?)", (anime_id, name))
    conn.commit()
    conn.close()

# Function to add episodes
def add_episode(anime_id, episode, m3u8):
    conn = sqlite3.connect(SQLITE_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO episodes (anime_id, episode, m3u8) VALUES (?, ?, ?)", (anime_id, episode, m3u8))
    conn.commit()
    conn.close()

# Function to fetch anime episodes
def get_anime_episodes(anime_id):
    conn = sqlite3.connect(SQLITE_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT episode, m3u8 FROM episodes WHERE anime_id=?", (anime_id,))
    results = cursor.fetchall()
    conn.close()

    return [{"episode": row[0], "m3u8": row[1]} for row in results] if results else None

# Function to search anime
def search_anime(query):
    conn = sqlite3.connect(SQLITE_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM anime WHERE LOWER(name) LIKE ?", ('%' + query.lower() + '%',))
    results = cursor.fetchall()
    conn.close()

    return [{"id": row[0], "name": row[1]} for row in results] if results else []

# HTTP Server Handler
class AnimeServer(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/add_anime":
            content_length = int(self.headers["Content-Length"])
            post_data = self.rfile.read(content_length).decode("utf-8")
            params = urllib.parse.parse_qs(post_data)

            anime_id = params.get("id", [""])[0]
            name = params.get("name", [""])[0]

            if anime_id and name:
                add_anime(anime_id, name)
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"Anime added successfully!")
            else:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Missing parameters!")

        elif self.path == "/add_episode":
            content_length = int(self.headers["Content-Length"])
            post_data = self.rfile.read(content_length).decode("utf-8")
            params = urllib.parse.parse_qs(post_data)

            anime_id = params.get("id", [""])[0]
            episode = params.get("episode", [""])[0]
            m3u8 = params.get("m3u8", [""])[0]

            if anime_id and episode and m3u8:
                add_episode(anime_id, episode, m3u8)
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"Episode added successfully!")
            else:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Missing parameters!")

    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed_path.query)

        if parsed_path.path == "/search_anime":
            query = params.get("query", [""])[0]
            results = search_anime(query)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(results).encode("utf-8"))

        elif parsed_path.path == "/get_episodes":
            anime_id = params.get("id", [""])[0]
            episodes = get_anime_episodes(anime_id)

            self.send_response(200 if episodes else 404)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(episodes or {"error": "No episodes found"}).encode("utf-8"))

# Run the server
if __name__ == "__main__":
    server_address = ("", 8080)
    httpd = HTTPServer(server_address, AnimeServer)
    print("Server running on port 8080...")
    httpd.serve_forever()
