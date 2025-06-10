import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

# Get all current column names
cursor.execute("""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_name = 'apollo_table'
""")
columns = cursor.fetchall()

print("Current columns:")
for col in columns:
    print(f"  {col[0]}")

# Rename each column to lowercase
print("\nRenaming columns to lowercase...")
for col in columns:
    old_name = col[0]
    new_name = old_name.lower().replace(' ', '_').replace('#_', 'num_')
    
    if old_name != new_name:
        try:
            cursor.execute(f'ALTER TABLE apollo_table RENAME COLUMN "{old_name}" TO {new_name}')
            print(f"  {old_name} → {new_name}")
        except Exception as e:
            print(f"  Error renaming {old_name}: {e}")

conn.commit()

# Show new column names
cursor.execute("""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_name = 'apollo_table'
    ORDER BY ordinal_position
""")
new_columns = cursor.fetchall()

print("\nNew column names:")
for col in new_columns:
    print(f"  {col[0]}")

cursor.close()
conn.close()
print("\nMigration complete!")