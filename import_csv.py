import pandas as pd
import sqlite3

# Configuration
CSV_FILE = r"C:\Users\zachw\Downloads\apollo-accounts-export (1).csv"  # Replace with your CSV filename
DB_PATH = r"C:\Users\zachw\Trailhead Partners\Trailhead Sharepoint - Documents\Applications\company_industries.db"

# Read CSV
print("Reading CSV file...")
df = pd.read_csv(CSV_FILE)
print(f"CSV contains {len(df)} rows")

# Connect to database
conn = sqlite3.connect(DB_PATH)

# Clear existing data (optional - comment out if you want to append)
cursor = conn.cursor()
cursor.execute("DELETE FROM 'apollo table'")
conn.commit()
print("Cleared existing data")

# Import all data
print("Importing data...")
df.to_sql('apollo table', conn, if_exists='append', index=False)

# Verify import
cursor.execute("SELECT COUNT(*) FROM 'apollo table'")
count = cursor.fetchone()[0]
print(f"Database now contains {count} rows")

conn.close()