import sqlite3

conn = sqlite3.connect('sinema_chatbot.db')
cursor = conn.cursor()

cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table'")
rows = cursor.fetchall()

with open('schema_output.txt', 'w') as f:
    for name, sql in rows:
        f.write(f"--- {name} ---\n")
        f.write(str(sql) + "\n\n")

print("Schema saved to schema_output.txt")
conn.close()
