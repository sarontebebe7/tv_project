
from flask import Flask, jsonify, request
import sqlite3

app = Flask(__name__)
DB_PATH = 'tvguide.db'

@app.route('/programs', methods=['GET'])
def get_programs():
    channel = request.args.get('channel')
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    if channel:
        cur.execute('SELECT * FROM tv_programs WHERE title != "" AND channel = ?', (channel,))
    else:
        cur.execute('SELECT * FROM tv_programs WHERE title != ""')
    rows = cur.fetchall()
    conn.close()
    programs = [dict(row) for row in rows]
    return jsonify(programs)

@app.route('/channel_counts', methods=['GET'])
def channel_counts():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT channel, COUNT(*) FROM tv_programs WHERE title != "" GROUP BY channel')
    counts = cur.fetchall()
    conn.close()
    return jsonify({channel: count for channel, count in counts})

@app.route('/')
def index():
    return "TV Guide API is running. Use /programs for data, /channel_counts for channel summary."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
