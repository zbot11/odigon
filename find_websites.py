import os
import sqlite3
import time
from datetime import datetime
from perplexity_api_enhanced import query_perplexity_with_website

# Database configuration
DB_PATH = r"C:\Users\zachw\Trailhead Partners\Trailhead Sharepoint - Documents\Applications\company_industries.db"

# Connect to the database
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# First, check how many need websites
cursor.execute("SELECT COUNT(*) FROM 'apollo table' WHERE (Website IS NULL OR Website = '') AND Status IS NULL")
need_processing = cursor.fetchone()[0]
print(f"Companies without websites that need processing: {need_processing}")

# Query to fetch companies without websites
query = """
SELECT Company, "Company City", "Company State"
FROM 'apollo table'
WHERE (Website IS NULL OR Website = '') 
AND Company IS NOT NULL
"""

cursor.execute(query)
rows = cursor.fetchall()

print(f"Found {len(rows)} companies to process")

# Process companies
for i, (company, city, state) in enumerate(rows):
    print(f"\nProcessing {i+1}/{len(rows)}: {company}, {city}, {state}")
    
    result, website = query_perplexity_with_website(company, city, state)
    print(f"Result: {result}")
    print(f"Website found: {website}")
    
    # Update both Status and Website in the database
    update_query = """
    UPDATE 'apollo table' 
    SET Status = ?, Website = ?
    WHERE Company = ? AND "Company City" = ? AND "Company State" = ?
    """
    
    cursor.execute(update_query, (result, website, company, city, state))
    conn.commit()
    
    print(f"Updated database for {company}")
    
    # Add delay to avoid rate limiting
    if i < len(rows) - 1:
        time.sleep(1)

conn.close()
print(f"\nProcessing complete! Processed {len(rows)} companies without websites.")