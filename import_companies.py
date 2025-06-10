#!/usr/bin/env python3
"""
Import companies from CSV file to PostgreSQL database
Usage: python import_companies.py <csv_file>
"""

import sys
from database_operations import import_csv_file, get_database_stats

def main():
    if len(sys.argv) < 2:
        print("Usage: python import_companies.py <csv_file>")
        print("Example: python import_companies.py apollo-accounts-export.csv")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    
    # Show current stats
    print("Current database statistics:")
    stats = get_database_stats()
    print(f"  Total companies: {stats['total_companies']}")
    print(f"  Missing websites: {stats['missing_websites']}")
    print(f"  Processed companies: {stats['processed_companies']}")
    print()
    
    # Import CSV
    print(f"Importing CSV file: {csv_file}")
    success, message, details = import_csv_file(file_path=csv_file)
    
    if success:
        print(f"✓ {message}")
        if details:
            print(f"  Rows imported: {details.get('rows_imported', 'N/A')}")
            if 'original_columns' in details and 'cleaned_columns' in details:
                print("\nColumn mapping:")
                for orig, clean in zip(details['original_columns'], details['cleaned_columns']):
                    if orig != clean:
                        print(f"  '{orig}' -> '{clean}'")
    else:
        print(f"✗ {message}")
        sys.exit(1)
    
    # Show updated stats
    print("\nUpdated database statistics:")
    stats = get_database_stats()
    print(f"  Total companies: {stats['total_companies']}")
    print(f"  Missing websites: {stats['missing_websites']}")
    print(f"  Processed companies: {stats['processed_companies']}")

if __name__ == "__main__":
    main()