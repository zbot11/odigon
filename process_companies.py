import os
import time
from dotenv import load_dotenv
import psycopg2
from perplexity_api import query_perplexity
from config import PROMPTS

load_dotenv()

# Get the prompt to use (can be set via environment variable)
PROMPT_NAME = os.getenv('PROMPT_NAME', 'default')
CLASSIFICATION_PROMPT = PROMPTS.get(PROMPT_NAME, PROMPTS['default'])

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL')

# Connect to the database
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

# Check how many already processed
cursor.execute("SELECT COUNT(*) FROM apollo_table WHERE status IS NOT NULL")
already_processed = cursor.fetchone()[0]
print(f"Already processed: {already_processed} companies")

# Query to fetch companies - only where status is NULL
query = """
SELECT company, website 
FROM apollo_table
WHERE company IS NOT NULL 
AND website IS NOT NULL 
AND status IS NULL
"""

cursor.execute(query)
rows = cursor.fetchall()

print(f"Remaining to process: {len(rows)} companies")
print(f"Using prompt: {PROMPT_NAME}")

# Process companies
for i, (company, website) in enumerate(rows):
    print(f"\nProcessing {i+1}/{len(rows)}: {company}")
    
    result = query_perplexity(company, website, CLASSIFICATION_PROMPT)
    print(f"Result: {result}")
    
    # Update status
    update_query = """
    UPDATE apollo_table 
    SET status = %s 
    WHERE company = %s AND website = %s
    """
    
    cursor.execute(update_query, (result, company, website))
    conn.commit()
    
    print(f"Updated database for {company}")
    
    if i < len(rows) - 1:
        time.sleep(1)

conn.close()
print(f"\nProcessing complete! Status updated for {len(rows)} companies.")