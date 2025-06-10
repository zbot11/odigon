import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

# Create the apollo_table with all your columns
create_table_query = '''
CREATE TABLE IF NOT EXISTS apollo_table (
    id SERIAL PRIMARY KEY,
    "Company" TEXT,
    "Company Name for Emails" TEXT,
    "Account Stage" TEXT,
    "Lists" TEXT,
    "# Employees" TEXT,
    "Industry" TEXT,
    "Account Owner" TEXT,
    "Website" TEXT,
    "Company Linkedin Url" TEXT,
    "Facebook Url" TEXT,
    "Twitter Url" TEXT,
    "Company Street" TEXT,
    "Company City" TEXT,
    "Company State" TEXT,
    "Company Country" TEXT,
    "Company Postal Code" TEXT,
    "Company Address" TEXT,
    "Keywords" TEXT,
    "Company Phone" TEXT,
    "SEO Description" TEXT,
    "Technologies" TEXT,
    "Total Funding" TEXT,
    "Latest Funding" TEXT,
    "Latest Funding Amount" TEXT,
    "Last Raised At" TEXT,
    "Annual Revenue" TEXT,
    "Number of Retail Locations" TEXT,
    "Apollo Account Id" TEXT,
    "SIC Codes" TEXT,
    "Short Description" TEXT,
    "Founded Year" TEXT,
    "Logo Url" TEXT,
    "Subsidiary of" TEXT,
    "Primary Intent Topic" TEXT,
    "Primary Intent Score" TEXT,
    "Secondary Intent Topic" TEXT,
    "Secondary Intent Score" TEXT,
    "Status" TEXT,
    "Notes1" TEXT,
    "Notes2" TEXT,
    "Notes3" TEXT
);
'''

cursor.execute(create_table_query)
conn.commit()

print("Table created successfully!")

cursor.close()
conn.close()