import os
import sqlite3
import time
from datetime import datetime
from perplexity_api import query_perplexity

# Database configuration
DB_PATH = r"C:\Users\zachw\Trailhead Partners\Trailhead Sharepoint - Documents\Applications\company_industries.db"

# Connect to the database
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# First, check how many have already been processed
cursor.execute("SELECT COUNT(*) FROM 'apollo table' WHERE Status IS NOT NULL")
already_processed = cursor.fetchone()[0]
print(f"Already processed: {already_processed} companies")


# Query to fetch Company and Website - LIMIT 5 for testing
query = """
SELECT Company, Website 
FROM 'apollo table'
WHERE Company IS NOT NULL AND Website IS NOT NULL AND Status IS NULL
"""

cursor.execute(query)
rows = cursor.fetchall()

print(f"Remaining to process: {len(rows)} companies")

# Process companies and update database
for i, (company, website) in enumerate(rows):
    print(f"\nProcessing {i+1}/{len(rows)}: {company}")
    
    result = query_perplexity(company, website)
    print(f"Result: {result}")
    
    # Update the Status column in the database
    update_query = """
    UPDATE 'apollo table' 
    SET Status = ? 
    WHERE Company = ? AND Website = ?
    """
    
    cursor.execute(update_query, (result, company, website))
    conn.commit()
    
    print(f"Updated database for {company}")
    
    # Add a small delay to avoid rate limiting
    if i < len(rows) - 1:  # Don't wait after the last company
        time.sleep(1)

conn.close()
print(f"\nProcessing complete! Status column updated for {len(rows)} companies.")
print(f"Total processed in database: {already_processed + len(rows)} companies")