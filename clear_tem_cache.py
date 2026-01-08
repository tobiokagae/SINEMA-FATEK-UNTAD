import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

conn = pymysql.connect(
    host=os.getenv('DB_HOST', '127.0.0.1'),
    user=os.getenv('DB_USERNAME', 'root'),
    password=os.getenv('DB_PASSWORD', ''),
    database=os.getenv('DB_DATABASE', 'siny1585_sinemadb')
)

cursor = conn.cursor()

# Delete cache entries for TEM queries
cursor.execute("DELETE FROM cache_chatbot WHERE query LIKE '%TEM%' OR query LIKE '%transkrip%'")
deleted = cursor.rowcount
conn.commit()

print(f"Deleted {deleted} cache entries related to TEM/transkrip")

cursor.close()
conn.close()
