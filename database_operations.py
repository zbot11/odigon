import os
import pandas as pd
import psycopg2
from sqlalchemy import create_engine
import re
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

def clean_column_name(col):
    """Convert column name to PostgreSQL-friendly format"""
    # Convert to lowercase
    col = col.lower()
    # Replace special characters with underscores
    col = re.sub(r'[^\w\s]', '_', col)
    # Replace spaces with underscores
    col = re.sub(r'\s+', '_', col)
    # Remove leading/trailing underscores
    col = col.strip('_')
    # Replace multiple underscores with single
    col = re.sub(r'_+', '_', col)
    return col

def get_database_stats():
    """Get statistics about the database"""
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT COUNT(*) FROM apollo_table")
        total_companies = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM apollo_table WHERE website IS NULL OR website = ''")
        missing_websites = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM apollo_table WHERE status IS NOT NULL")
        processed_companies = cursor.fetchone()[0]
        
        return {
            'total_companies': total_companies,
            'missing_websites': missing_websites,
            'processed_companies': processed_companies
        }
    finally:
        conn.close()

def truncate_database():
    """Truncate the apollo_table"""
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    try:
        cursor.execute("TRUNCATE TABLE apollo_table")
        conn.commit()
        return True, "Database truncated successfully"
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()

def import_csv_file(file_path=None, file_object=None):
    """Import CSV file to database
    
    Args:
        file_path: Path to CSV file (for local files)
        file_object: File object (for uploaded files)
    
    Returns:
        tuple: (success, message, details)
    """
    try:
        # Read CSV from either file path or file object
        if file_path:
            df = pd.read_csv(file_path)
        elif file_object:
            df = pd.read_csv(file_object)
        else:
            return False, "No file provided", {}
        
        original_rows = len(df)
        original_columns = df.columns.tolist()
        
        # Clean column names
        df.columns = [clean_column_name(col) for col in df.columns]
        cleaned_columns = df.columns.tolist()
        
        # Create engine and import
        engine = create_engine(DATABASE_URL)
        df.to_sql('apollo_table', engine, if_exists='append', index=False, method='multi', chunksize=500)
        
        return True, f"Successfully imported {original_rows} rows", {
            'rows_imported': original_rows,
            'original_columns': original_columns,
            'cleaned_columns': cleaned_columns
        }
        
    except Exception as e:
        return False, f"Import failed: {str(e)}", {}

def find_websites_task(status_dict):
    """Find websites for companies that don't have them"""
    from perplexity_find_website import find_website
    import time
    
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    try:
        # Get companies without websites
        cursor.execute("""
            SELECT company, company_city, company_state
            FROM apollo_table
            WHERE (website IS NULL OR website = '') 
            AND company IS NOT NULL
        """)
        
        rows = cursor.fetchall()
        total = len(rows)
        status_dict['total'] = total
        
        for i, (company, city, state) in enumerate(rows):
            status_dict['progress'] = i + 1
            
            website = find_website(company, city, state)
            
            if website:
                cursor.execute("""
                    UPDATE apollo_table 
                    SET website = %s
                    WHERE company = %s AND company_city = %s AND company_state = %s
                """, (website, company, city, state))
                conn.commit()
            
            # Rate limiting
            if i < total - 1:
                time.sleep(1)
                
    finally:
        conn.close()

def classify_companies_task(status_dict):
    """Classify companies based on their websites"""
    from perplexity_api import query_perplexity
    from config import PROMPTS
    import time
    
    # Get the prompt
    PROMPT_NAME = os.getenv('PROMPT_NAME', 'default')
    CLASSIFICATION_PROMPT = PROMPTS.get(PROMPT_NAME, PROMPTS['default'])
    
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    try:
        # Get unprocessed companies with websites
        cursor.execute("""
            SELECT company, website 
            FROM apollo_table
            WHERE company IS NOT NULL 
            AND website IS NOT NULL 
            AND status IS NULL
        """)
        
        rows = cursor.fetchall()
        total = len(rows)
        status_dict['total'] = total
        
        for i, (company, website) in enumerate(rows):
            status_dict['progress'] = i + 1
            
            result = query_perplexity(company, website, CLASSIFICATION_PROMPT)
            
            if result:
                cursor.execute("""
                    UPDATE apollo_table 
                    SET status = %s 
                    WHERE company = %s AND website = %s
                """, (result, company, website))
                conn.commit()
            
            # Rate limiting
            if i < total - 1:
                time.sleep(1)
                
    finally:
        conn.close()

def get_companies_for_export(status_filter=None):
    """Get companies for export with optional filtering"""
    conn = psycopg2.connect(DATABASE_URL)
    
    try:
        if status_filter:
            query = "SELECT * FROM apollo_table WHERE status = %s"
            df = pd.read_sql_query(query, conn, params=(status_filter,))
        else:
            query = "SELECT * FROM apollo_table"
            df = pd.read_sql_query(query, conn)
        
        return df
    finally:
        conn.close()

# Utility function for testing
if __name__ == "__main__":
    stats = get_database_stats()
    print("Database Statistics:")
    print(f"Total companies: {stats['total_companies']}")
    print(f"Missing websites: {stats['missing_websites']}")
    print(f"Processed companies: {stats['processed_companies']}")