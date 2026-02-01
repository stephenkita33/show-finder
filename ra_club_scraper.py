"""
Resident Advisor Club Events Scraper
Uses RA.co's GraphQL API to fetch events for a specific club/venue.

Usage:
    python ra_club_scraper.py <club_id> [-o output.csv]
    
Example:
    python ra_club_scraper.py 105873 -o events.csv
"""

import requests
import pandas as pd
import argparse
import json
from datetime import datetime, timedelta


# RA.co GraphQL endpoint
GRAPHQL_URL = "https://ra.co/graphql"

# Headers to mimic a browser request
HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "Origin": "https://ra.co",
    "Referer": "https://ra.co/",
}


def get_club_events(club_id: int, limit: int = 100) -> dict:
    """
    Fetch upcoming events for a specific club using RA's GraphQL API.
    
    Args:
        club_id: The RA club ID
        limit: Max number of events to fetch
    
    Returns:
        Dict containing the GraphQL response
    """
    
    # GraphQL query for upcoming events
    query = """
    query GET_VENUE_UPCOMING($id: ID!, $limit: Int) {
        venue(id: $id) {
            id
            name
            address
            events(type: LATEST, limit: $limit) {
                id
                title
                date
                startTime
                endTime
                contentUrl
                flyerFront
                artists {
                    id
                    name
                }
                pick {
                    blurb
                }
            }
        }
    }
    """
    
    variables = {
        "id": str(club_id),
        "limit": limit
    }
    
    payload = {
        "query": query,
        "variables": variables
    }
    
    response = requests.post(GRAPHQL_URL, headers=HEADERS, json=payload)
    response.raise_for_status()
    
    return response.json()


def get_club_past_events(club_id: int, limit: int = 100) -> dict:
    """
    Fetch past events for a specific club.
    """
    
    query = """
    query GET_VENUE_PAST($id: ID!, $limit: Int) {
        venue(id: $id) {
            id
            name
            address
            events(type: PREVIOUS, limit: $limit) {
                id
                title
                date
                startTime
                endTime
                contentUrl
                flyerFront
                artists {
                    id
                    name
                }
                pick {
                    blurb
                }
            }
        }
    }
    """
    
    variables = {
        "id": str(club_id),
        "limit": limit
    }
    
    payload = {
        "query": query,
        "variables": variables
    }
    
    response = requests.post(GRAPHQL_URL, headers=HEADERS, json=payload)
    response.raise_for_status()
    
    return response.json()


def parse_events(response_data: dict) -> list:
    """
    Parse the GraphQL response into a list of event dictionaries.
    
    Args:
        response_data: The GraphQL response
    
    Returns:
        List of event dictionaries
    """
    events = []
    
    venue_data = response_data.get("data", {}).get("venue")
    if not venue_data:
        return events
    
    venue_name = venue_data.get("name", "")
    venue_address = venue_data.get("address", "")
    
    # Events list is directly in 'events', no 'data' wrapper anymore
    events_list = venue_data.get("events", [])
    
    for event in events_list:
        # Extract artist names
        artists = event.get("artists", []) or []
        artist_names = ", ".join([a.get("name", "") for a in artists if a.get("name")])
        
        # Get description from pick blurb if available
        description = ""
        if event.get("pick") and event["pick"].get("blurb"):
            description = event["pick"]["blurb"]
        
        events.append({
            "event_id": event.get("id"),
            "title": event.get("title"),
            "date": event.get("date"),
            "start_time": event.get("startTime"),
            "end_time": event.get("endTime"),
            "venue": venue_name,
            "venue_address": venue_address,
            "performers": artist_names,
            "description": description,
            "url": f"https://ra.co{event.get('contentUrl', '')}" if event.get("contentUrl") else "",
            "flyer_url": event.get("flyerFront", "")
        })
    
    return events


def fetch_all_club_events(club_id: int, include_past: bool = False, max_pages: int = 10) -> pd.DataFrame:
    """
    Fetch all events (upcoming and optionally past) for a club.
    
    Args:
        club_id: The RA club ID
        include_past: Whether to include past events
        max_pages: Used to calculate limit (50 * max_pages) to mimic old behavior
    
    Returns:
        DataFrame containing all events
    """
    all_events = []
    limit = max_pages * 50
    
    # Fetch upcoming events
    print(f"Fetching upcoming events for club {club_id}...")
    try:
        response = get_club_events(club_id, limit=limit)
        events = parse_events(response)
        
        if events:
            all_events.extend(events)
            print(f"  Found {len(events)} upcoming events")
        else:
            print("  No upcoming events found")
            
    except Exception as e:
        print(f"  Error fetching upcoming events: {e}")
    
    # Fetch past events
    if include_past:
        print(f"Fetching past events for club {club_id}...")
        try:
            response = get_club_past_events(club_id, limit=limit)
            events = parse_events(response)
            
            if events:
                all_events.extend(events)
                print(f"  Found {len(events)} past events")
            else:
                print("  No past events found")
                
        except Exception as e:
            print(f"  Error fetching past events: {e}")
    
    # Create DataFrame
    df = pd.DataFrame(all_events)
    
    # Sort by date
    if not df.empty and "date" in df.columns:
        df = df.sort_values("date", ascending=False)
    
    return df


def main():
    parser = argparse.ArgumentParser(
        description="Scrape event data from a Resident Advisor club page"
    )
    parser.add_argument(
        "club_id",
        type=int,
        nargs="?",
        default=105873,
        help="The club ID from the RA URL (e.g., 105873 from ra.co/clubs/105873)"
    )
    parser.add_argument(
        "-o", "--output",
        default="events.csv",
        help="Output file path (default: events.csv). Supports .csv and .json"
    )
    parser.add_argument(
        "--include-past",
        action="store_true",
        help="Fetch past events in addition to upcoming events"
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=10,
        help="Maximum number of pages to fetch per category (default: 10)"
    )
    
    args = parser.parse_args()
    
    # Fetch events
    df = fetch_all_club_events(
        club_id=args.club_id,
        include_past=args.include_past,
        max_pages=args.max_pages
    )
    
    print(f"\nTotal events found: {len(df)}")
    
    if df.empty:
        print("No events found. The club ID might be invalid or there are no events.")
        return
    
    # Save to file
    output_path = args.output
    if output_path.endswith(".json"):
        df.to_json(output_path, orient="records", indent=2)
    else:
        df.to_csv(output_path, index=False)
    
    print(f"Events saved to: {output_path}")
    
    # Print sample
    print("\nSample of fetched data:")
    print(df[["date", "title", "performers"]].head(5).to_string())


if __name__ == "__main__":
    main()
