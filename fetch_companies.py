import os
import sqlite3
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DB_PATH = r"C:\Users\zachw\Trailhead Partners\Trailhead Sharepoint - Documents\Applications\company_industries.db"

# Connect to the database
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Query to fetch Company and Website
query = """
SELECT Company, Website 
FROM 'apollo table'
WHERE Company IS NOT NULL AND Website IS NOT NULL
"""

# Execute query and fetch results
cursor.execute(query)
rows = cursor.fetchall()

print(f"Found {len(rows)} companies to process")

