import sqlite3
import pandas as pd
import re
from datetime import datetime

def sanitize_table_name(venue_name: str) -> str:
    """
    Sanitize venue name to create a valid and clean SQL table name.
    Example: "Nowadays" -> "events_nowadays"
             "Public Records" -> "events_public_records"
    """
    # Convert to lowercase
    name = venue_name.lower()
    # Replace non-alphanumeric characters with underscores
    name = re.sub(r'[^a-z0-9]+', '_', name)
    # Remove leading/trailing underscores
    name = name.strip('_')
    
    return f"events_{name}"

def save_events(pd_events: pd.DataFrame, db_path: str, venue_name: str):
    """
    Save events DataFrame to a SQLite database.
    Creates a new table for the venue if it doesn't exist.
    """
    if pd_events.empty:
        print("No events to save to database.")
        return

    table_name = sanitize_table_name(venue_name)
    
    conn = sqlite3.connect(db_path)
    try:
        # Create table if it doesn't exist
        # We manually define schema to ensure types and primary key
        # SQLite doesn't strictly enforce types, but it's good practice
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            event_id TEXT PRIMARY KEY,
            title TEXT,
            date TEXT,
            start_time TEXT,
            end_time TEXT,
            venue TEXT,
            venue_address TEXT,
            performers TEXT,
            description TEXT,
            url TEXT,
            flyer_url TEXT,
            updated_at TIMESTAMP
        )
        """
        conn.execute(create_table_sql)
        
        # Add updated_at timestamp
        pd_events = pd_events.copy()
        pd_events['updated_at'] = datetime.now().isoformat()
        
        # Prepare data for insertion (list of dictionaries)
        events_data = pd_events.to_dict(orient='records')
        
        # Insert or Replace logic
        # We construct the INSERT OR REPLACE statement dynamically based on columns
        columns = [
            'event_id', 'title', 'date', 'start_time', 'end_time', 
            'venue', 'venue_address', 'performers', 'description', 
            'url', 'flyer_url', 'updated_at'
        ]
        
        placeholders = ', '.join(['?'] * len(columns))
        col_names = ', '.join(columns)
        
        sql = f"INSERT OR REPLACE INTO {table_name} ({col_names}) VALUES ({placeholders})"
        
        # Extract values in the correct order for each row
        values = []
        for row in events_data:
            values.append([row.get(col) for col in columns])
            
        conn.executemany(sql, values)
        conn.commit()
        
        print(f"Saved {len(pd_events)} events to table '{table_name}' in {db_path}")
        
    except Exception as e:
        print(f"Error saving events to database: {e}")
        # Re-raise to let the caller know
        raise
    finally:
        conn.close()
