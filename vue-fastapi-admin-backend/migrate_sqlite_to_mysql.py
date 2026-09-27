"""
SQLite to MySQL Migration Script
================================
This script migrates data from SQLite database to MySQL database.
It uses pandas for data transfer and handles common data type conversions.

Usage:
    python migrate_sqlite_to_mysql.py

Prerequisites:
    pip install pandas sqlalchemy pymysql aiosqlite
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    import pandas as pd
    from sqlalchemy import create_engine, inspect
    import sqlite3
    import pymysql
except ImportError as e:
    print(f"Error: Missing required dependencies. Please install them:")
    print(f"  pip install pandas sqlalchemy pymysql")
    sys.exit(1)


def get_sqlite_tables(sqlite_db_path):
    """Get all table names from SQLite database"""
    conn = sqlite3.connect(sqlite_db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    return tables


def get_table_schema(sqlite_db_path, table_name):
    """Get table schema from SQLite"""
    conn = sqlite3.connect(sqlite_db_path)
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = cursor.fetchall()
    conn.close()
    return columns


def read_sqlite_data(sqlite_db_path, table_name):
    """Read all data from a SQLite table"""
    conn = sqlite3.connect(sqlite_db_path)
    df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
    conn.close()
    return df


def write_mysql_data(df, mysql_url, table_name, if_exists='replace'):
    """Write data to MySQL table"""
    engine = create_engine(mysql_url)
    
    # Handle special cases for data types
    for column in df.columns:
        # Convert boolean values to integers for better MySQL compatibility
        if df[column].dtype == 'bool':
            df[column] = df[column].astype(int)
        
        # Handle datetime objects
        if pd.api.types.is_datetime64_any_dtype(df[column]):
            df[column] = df[column].dt.strftime('%Y-%m-%d %H:%M:%S')
    
    # Write to MySQL
    df.to_sql(table_name, engine, if_exists=if_exists, index=False)
    print(f"  ✓ Migrated {len(df)} rows to '{table_name}'")


def migrate_database(sqlite_db_path, mysql_config):
    """Main migration function"""
    
    # Build MySQL connection URL
    mysql_url = (
        f"mysql+pymysql://{mysql_config['user']}:{mysql_config['password']}"
        f"@{mysql_config['host']}:{mysql_config['port']}/{mysql_config['database']}"
        f"?charset=utf8mb4"
    )
    
    print("=" * 60)
    print("SQLite to MySQL Migration Tool")
    print("=" * 60)
    print(f"\nSource: {sqlite_db_path}")
    print(f"Target: {mysql_config['host']}:{mysql_config['port']}/{mysql_config['database']}")
    print("\n" + "=" * 60)
    
    # Check if SQLite database exists
    if not os.path.exists(sqlite_db_path):
        print(f"\n✗ Error: SQLite database not found at {sqlite_db_path}")
        sys.exit(1)
    
    # Get all tables from SQLite
    tables = get_sqlite_tables(sqlite_db_path)
    print(f"\nFound {len(tables)} tables in SQLite database:")
    for table in tables:
        print(f"  - {table}")
    
    # Create MySQL database if it doesn't exist
    try:
        # Connect without specifying database to create it
        temp_conn = pymysql.connect(
            host=mysql_config['host'],
            port=mysql_config['port'],
            user=mysql_config['user'],
            password=mysql_config['password']
        )
        cursor = temp_conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{mysql_config['database']}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        temp_conn.close()
        print(f"\n✓ MySQL database '{mysql_config['database']}' is ready")
    except Exception as e:
        print(f"\n✗ Error creating MySQL database: {e}")
        sys.exit(1)
    
    # Migrate each table
    print("\nStarting migration...")
    migrated_count = 0
    failed_tables = []
    
    for table_name in tables:
        try:
            print(f"\nMigrating table: {table_name}")
            
            # Read data from SQLite
            df = read_sqlite_data(sqlite_db_path, table_name)
            
            if df.empty:
                print(f"  ⚠ Table '{table_name}' is empty, skipping...")
                continue
            
            # Write to MySQL
            write_mysql_data(df, mysql_url, table_name, if_exists='replace')
            migrated_count += 1
            
        except Exception as e:
            print(f"  ✗ Failed to migrate '{table_name}': {e}")
            failed_tables.append(table_name)
    
    # Print summary
    print("\n" + "=" * 60)
    print("Migration Summary")
    print("=" * 60)
    print(f"Total tables: {len(tables)}")
    print(f"Successfully migrated: {migrated_count}")
    print(f"Failed: {len(failed_tables)}")
    
    if failed_tables:
        print("\nFailed tables:")
        for table in failed_tables:
            print(f"  - {table}")
    
    print("\n" + "=" * 60)
    if len(failed_tables) == 0:
        print("✓ Migration completed successfully!")
    else:
        print("⚠ Migration completed with errors. Please check the failed tables above.")
    print("=" * 60)


def main():
    """Entry point"""
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Get configuration
    base_dir = project_root
    sqlite_db_path = os.path.join(base_dir, "db.sqlite3")
    
    mysql_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', '3306')),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', ''),
        'database': os.getenv('DB_NAME', 'vue_fastapi_admin'),
    }
    
    # Confirm migration
    print("\nWARNING: This will overwrite existing data in MySQL!")
    print(f"MySQL Database: {mysql_config['database']}")
    confirm = input("\nType 'yes' to continue with migration: ")
    
    if confirm.lower() != 'yes':
        print("Migration cancelled.")
        sys.exit(0)
    
    # Run migration
    migrate_database(sqlite_db_path, mysql_config)


if __name__ == "__main__":
    main()
