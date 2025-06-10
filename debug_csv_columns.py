#!/usr/bin/env python3
"""
Debug CSV column names and their transformations
Usage: python debug_csv_columns.py <csv_file>
"""

import sys
import pandas as pd
from database_operations import clean_column_name, DATABASE_URL
import psycopg2

def main():
    if len(sys.argv) < 2:
        print("Usage: python debug_csv_columns.py <csv_file>")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    
    # Read CSV headers
    print(f"Reading CSV file: {csv_file}")
    df = pd.read_csv(csv_file, nrows=1)  # Just read header + 1 row
    
    # Get database columns
    print("\nGetting database columns...")
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'apollo_table' 
        ORDER BY ordinal_position
    """)
    db_columns = [col[0] for col in cursor.fetchall()]
    conn.close()
    
    # Show transformations
    print("\nColumn Transformations:")
    print("-" * 80)
    print(f"{'CSV Column':<35} {'Cleaned':<35} {'In DB?':<10}")
    print("-" * 80)
    
    missing_columns = []
    
    for col in df.columns:
        cleaned = clean_column_name(col)
        in_db = cleaned in db_columns
        print(f"{col:<35} {cleaned:<35} {'✓' if in_db else '✗'}")
        
        if not in_db:
            missing_columns.append((col, cleaned))
    
    if missing_columns:
        print("\n⚠️  WARNING: The following columns don't match the database:")
        for orig, cleaned in missing_columns:
            print(f"   '{orig}' -> '{cleaned}' (not found in database)")
            # Suggest closest match
            suggestions = [db_col for db_col in db_columns if cleaned.lower() in db_col or db_col in cleaned.lower()]
            if suggestions:
                print(f"     Possible matches: {', '.join(suggestions)}")
    else:
        print("\n✓ All columns match the database schema!")
    
    # Show database columns not in CSV
    csv_cleaned_columns = [clean_column_name(col) for col in df.columns]
    db_only_columns = [col for col in db_columns if col not in csv_cleaned_columns and col not in ['id', 'status', 'notes1', 'notes2', 'notes3']]
    
    if db_only_columns:
        print(f"\nDatabase columns not in CSV: {', '.join(db_only_columns)}")

if __name__ == "__main__":
    main()