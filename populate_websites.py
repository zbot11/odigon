import os
import psycopg2
import time
from perplexity_find_website import find_website
from dotenv import load_dotenv

load_dotenv()

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL')

# Connect to the database
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

# Count companies without websites
cursor.execute("SELECT COUNT(*) FROM apollo_table WHERE (website IS NULL OR website = '')")
total_without_website = cursor.fetchone()[0]
print(f"Total companies without websites: {total_without_website}")

# Query to fetch companies without websites
query = """
SELECT company, company_city, company_state
FROM apollo_table
WHERE (website IS NULL OR website = '') 
AND company IS NOT NULL
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
        
        # Update website in the database
        update_query = """
        UPDATE apollo_table 
        SET website = %s
        WHERE company = %s AND company_city = %s AND company_state = %s
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