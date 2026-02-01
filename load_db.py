import argparse
import pandas as pd
import database
import sys
import os

def main():
    parser = argparse.ArgumentParser(
        description="Load event CSV data into SQLite database"
    )
    parser.add_argument(
        "csv_file",
        help="Path to the CSV file containing event data"
    )
    parser.add_argument(
        "--db",
        default="events.db",
        help="SQLite database path (default: events.db)"
    )
    
    args = parser.parse_args()
    
    if not os.path.exists(args.csv_file):
        print(f"Error: CSV file '{args.csv_file}' not found.")
        sys.exit(1)
        
    try:
        print(f"Reading events from {args.csv_file}...")
        df = pd.read_csv(args.csv_file)
        
        if df.empty:
            print("CSV file is empty. Nothing to load.")
            return

        # Infer venue name from the first row
        if "venue" in df.columns:
            venue_name = df.iloc[0]["venue"]
            print(f"Detected venue: {venue_name}")
        else:
            # Fallback if venue column is missing (should stick to file name or user input ideally)
            print("Warning: 'venue' column missing in CSV. Using 'unknown_venue'.")
            venue_name = "unknown_venue"
            
        print(f"Saving to database {args.db}...")
        database.save_events(df, args.db, venue_name)
        print("Done.")
        
    except Exception as e:
        print(f"Error loading data: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
