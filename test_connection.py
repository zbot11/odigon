import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

# Connect to database
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

# Get column names from apollo_table
cursor.execute("""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_name = 'apollo_table' 
    ORDER BY ordinal_position
""")

columns = cursor.fetchall()
column_list = [col[0] for col in columns]

print("PostgreSQL apollo_table columns:")
print("-" * 40)
for i, col in enumerate(column_list, 1):
    print(f"{i}. {col}")

conn.close()