import sqlite3

DB_PATH = "todo.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Check what columns exist
cursor.execute("PRAGMA table_info(task);")
columns = [col[1] for col in cursor.fetchall()]
print("Current columns:", columns)

if "overdue" not in columns:
    cursor.execute("ALTER TABLE task ADD COLUMN overdue BOOLEAN DEFAULT 0;")
    print("✅ Added 'overdue' column to task table")
else:
    print("ℹ️ 'overdue' column already exists")

conn.commit()
conn.close()
