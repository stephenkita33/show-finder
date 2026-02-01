# Show Finder

A Python-based toolset for scraping club events from Resident Advisor (RA.co) and acting as a local database for show finding. This project allows you to fetch upcoming (and past) events for specific venues, save them to CSV/JSON, and load them into a SQLite database for querying.

## Features

- **Scrape Events**: Fetch event data from RA.co for any venue using its Club ID.
- **Data Export**: Save scraped data to CSV or JSON formats.
- **Database Integration**: Load event data into a SQLite database (with automatic table creation per venue).
- **GraphQL API**: Uses RA's GraphQL API for structured and reliable data fetching.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/stephenkita33/show-finder.git
    cd show-finder
    ```

2.  **Install dependencies**:
    Ensure you have Python installed, then run:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

### 1. Scraping Events (`ra_club_scraper.py`)

This script scrapes events from a specific RA club page. You need the **Club ID**, which can be found in the RA URL (e.g., `ra.co/clubs/105873` -> ID is `105873`).

**Basic usage (saves to `events.csv` by default):**
```bash
python ra_club_scraper.py 105873
```

**Specify output file:**
```bash
python ra_club_scraper.py 105873 -o my_club_events.csv
```

**Include past events:**
```bash
python ra_club_scraper.py 105873 --include-past
```

**Options:**
- `club_id`: The ID of the club to scrape (default: 105873).
- `-o, --output`: Output file path (supports .csv and .json).
- `--include-past`: Fetch past events in addition to upcoming ones.
- `--max-pages`: Control how many pages of events to fetch (default: 10).

### 2. Loading Database (`load_db.py`)

Once you have a CSV file, you can load it into a SQLite database. This script automatically detects the venue name and creates/updates a corresponding table (e.g., `events_nowadays`).

```bash
python load_db.py events.csv
```

**Specify database file:**
```bash
python load_db.py events.csv --db my_shows.db
```

### 3. Debugging (`debug_scraper_response.py`)

A simple script to test valid GraphQL queries and inspect the available fields on the `Event` type from the RA API. useful for development or debugging API changes.

```bash
python debug_scraper_response.py
```

## Project Structure

- **`ra_club_scraper.py`**: Main scraper logic. Fetches data from RA GraphQL and saves to file.
- **`load_db.py`**: CLI tool to read a CSV and save it to the database.
- **`database.py`**: Database logic (table creation, insertion) used by `load_db.py`.
- **`debug_scraper_response.py`**: Utility for inspecting RA API schemas.
- **`requirements.txt`**: Python dependencies (`requests`, `pandas`).

## Database Schema

Tables are created dynamically based on the venue name (sanitized). The schema includes:
- `event_id` (Primary Key)
- `title`
- `date`, `start_time`, `end_time`
- `venue`, `venue_address`
- `performers`
- `description`
- `url`, `flyer_url`
- `updated_at`
