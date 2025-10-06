import sqlite3
import os
import re

db_path = "tvguide.db"
txt_files = [
    "tv_programs_bbc.txt",
    "tv_programs_disc.txt",
    "tv_programs_national.txt"
]

def parse_programs(file_path):
    with open(file_path, encoding="utf-8") as f:
        content = f.read()
    # Split by separator line
    entries = re.split(r"-+", content)
    programs = []
    expected_fields = [
        "Title", "Day", "Date", "Start Time", "End Time", "Duration", "Channel",
        "Link", "Original Name", "Year", "Description", "Score", "Genre"
    ]
    for entry in entries:
        lines = entry.strip().splitlines()
        if not lines:
            continue
        data = {}
        for line in lines:
            if ":" in line:
                key, value = line.split(":", 1)
                data[key.strip()] = value.strip()
        # Ensure all expected fields are present
        for field in expected_fields:
            if field not in data:
                data[field] = ""
        # Log entries with missing or mostly empty data
        if not data["Title"]:
            print(f"Warning: Entry missing Title in {file_path}: {data}")
        programs.append(data)
    return programs

def main():
    if os.path.exists(db_path):
        os.remove(db_path)
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE tv_programs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            day TEXT,
            date TEXT,
            start_time TEXT,
            end_time TEXT,
            duration TEXT,
            channel TEXT,
            link TEXT,
            original_name TEXT,
            year TEXT,
            description TEXT,
            score TEXT,
            genre TEXT,
            source_file TEXT
        )
    """)
    for txt_file in txt_files:
        programs = parse_programs(txt_file)
        print(f"First 3 parsed entries from {txt_file}:")
        for i, prog in enumerate(programs[:3]):
            print(prog)
        for prog in programs:
            # Only insert entries with non-empty Title and Channel
            if prog.get("Title", "") and prog.get("Channel", ""):
                c.execute("""
                    INSERT INTO tv_programs (
                        title, day, date, start_time, end_time, duration, channel, link, original_name, year, description, score, genre, source_file
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    prog.get("Title", ""),
                    prog.get("Day", ""),
                    prog.get("Date", ""),
                    prog.get("Start Time", ""),
                    prog.get("End Time", ""),
                    prog.get("Duration", ""),
                    prog.get("Channel", ""),
                    prog.get("Link", ""),
                    prog.get("Original Name", ""),
                    prog.get("Year", ""),
                    prog.get("Description", ""),
                    prog.get("Score", ""),
                    prog.get("Genre", ""),
                    txt_file
                ))
    conn.commit()
    conn.close()
    print("Database overwritten and populated with all TV programs.")

if __name__ == "__main__":
    main()
