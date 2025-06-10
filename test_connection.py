import psycopg2
import os

# Replace this with your External Database URL
DATABASE_URL = "postgresql://prod_db_y7wu_user:DAsk6RFgb8hmAgAuneniNof7yTFYmkLP@dpg-d148j4q4d50c7387f910-a.ohio-postgres.render.com/prod_db_y7wu"

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Test the connection
    cursor.execute("SELECT version();")
    record = cursor.fetchone()
    print("Connected to:", record[0])
    
    cursor.close()
    conn.close()
    print("\nConnection successful!")
    
except Exception as e:
    print("Connection failed:", e)