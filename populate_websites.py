import os
import sqlite3
import time
from perplexity_find_website import find_website

# Database configuration
DB_PATH = r"C:\Users\zachw\Trailhead Partners\Trailhead Sharepoint - Documents\Applications\company_industries.db"

# Connect to the database
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Count companies without websites
cursor.execute("SELECT COUNT(*) FROM 'apollo table' WHERE (Website IS NULL OR Website = '')")
total_without_website = cursor.fetchone()[0]
print(f"Total companies without websites: {total_without_website}")

# Query to fetch companies without websites
query = """
SELECT Company, "Company City", "Company State"
FROM 'apollo table'
WHERE (Website IS NULL OR Website = '') 
AND Company IS NOT NULL
"""

cursor.execute(query)
rows = cursor.fetchall()

print(f"Starting to find websites for {len(rows)} companies\n")

# Process companies
for i, (company, city, state) in enumerate(rows):
    print(f"Finding website {i+1}/{len(rows)}: {company}, {city}, {state}")
    
    website = find_website(company, city, state)
    
    if website:
        print(f"Found: {website}")
        
        # Update Website in the database
        update_query = """
        UPDATE 'apollo table' 
        SET Website = ?
        WHERE Company = ? AND "Company City" = ? AND "Company State" = ?
        """
        
        cursor.execute(update_query, (website, company, city, state))
        conn.commit()
    else:
        print(f"No website found")
    
    # Add delay to avoid rate limiting
    if i < len(rows) - 1:
        time.sleep(1)

conn.close()
print(f"\nWebsite search complete! Processed {len(rows)} companies.")