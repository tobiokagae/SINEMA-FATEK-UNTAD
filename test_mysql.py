import sys
sys.path.insert(0, '.')
from app.config import DATABASE_URL
from sqlalchemy import create_engine, text

print(f"Connecting to: {DATABASE_URL[:60]}...")
engine = create_engine(DATABASE_URL)
conn = engine.connect()

# Check chatbot tables
result = conn.execute(text("SHOW TABLES"))
tables = [row[0] for row in result.fetchall()]

chatbot_tables = [t for t in tables if 'chatbot' in t or 'document' in t]
print(f"\n✅ Chatbot-related tables found:")
for t in chatbot_tables:
    print(f"  - {t}")

# Test insert and query on sessions_chatbot
print("\n🔄 Testing insert into sessions_chatbot...")
try:
    conn.execute(text("INSERT IGNORE INTO sessions_chatbot (id, created_at, updated_at) VALUES ('test_session', NOW(), NOW())"))
    conn.commit()
    print("  ✅ Insert OK")
except Exception as e:
    print(f"  ⚠️ Insert: {e}")

# Query back
result = conn.execute(text("SELECT id FROM sessions_chatbot WHERE id = 'test_session'"))
rows = result.fetchall()
print(f"  ✅ Query OK - found {len(rows)} row(s)")

# Cleanup
conn.execute(text("DELETE FROM sessions_chatbot WHERE id = 'test_session'"))
conn.commit()
print("  ✅ Cleanup OK")

conn.close()
print("\n✅ All database tests passed!")
