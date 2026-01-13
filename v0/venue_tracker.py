#!/usr/bin/env python3
"""
NYC Concert Venue Tracker
Monitors venues in Manhattan, Brooklyn, and Queens for new show announcements.
Writes new events to a local file for manual checking.
"""

import requests
from bs4 import BeautifulSoup
import json
import os
import hashlib
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Optional
import re
import time

# Configuration
OUTPUT_FILE = "new_events.txt"
SEEN_EVENTS_FILE = "seen_events.json"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"

@dataclass
class Event:
    venue: str
    title: str
    date: str
    url: Optional[str] = None
    time: Optional[str] = None
    
    def event_id(self) -> str:
        """Generate unique ID for deduplication"""
        key = f"{self.venue}|{self.title}|{self.date}"
        return hashlib.md5(key.encode()).hexdigest()

def get_headers():
    return {"User-Agent": USER_AGENT}

def load_seen_events() -> set:
    """Load previously seen event IDs"""
    if os.path.exists(SEEN_EVENTS_FILE):
        with open(SEEN_EVENTS_FILE, 'r') as f:
            return set(json.load(f))
    return set()

def save_seen_events(seen: set):
    """Save seen event IDs"""
    with open(SEEN_EVENTS_FILE, 'w') as f:
        json.dump(list(seen), f)

def scrape_h0l0() -> list[Event]:
    """Scrape H0L0 events from h0l0.nyc/events"""
    events = []
    try:
        resp = requests.get("https://h0l0.nyc/events", headers=get_headers(), timeout=30)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Find event blocks - they have date and title info
        # Looking for patterns like "Thu, Jan 15 10:00pm" and event names
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            if '/event/' in href:
                # Get the parent container for more context
                parent = link.find_parent(['div', 'article', 'section'])
                if parent:
                    text = parent.get_text(' ', strip=True)
                    # Try to extract date and title
                    # Pattern: "Jan 15 10:00pm EVENT NAME"
                    title_elem = parent.find(['h6', 'h5', 'h4', 'h3', 'strong'])
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        # Try to find date
                        date_match = re.search(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[,\s]+\d{1,2}', text)
                        date_str = date_match.group(0) if date_match else "TBD"
                        
                        events.append(Event(
                            venue="H0L0",
                            title=title,
                            date=date_str,
                            url=f"https://h0l0.nyc{href}" if href.startswith('/') else href
                        ))
    except Exception as e:
        print(f"Error scraping H0L0: {e}")
    return events

def scrape_wonderville() -> list[Event]:
    """Scrape Wonderville events from wonderville.nyc/events"""
    events = []
    try:
        resp = requests.get("https://www.wonderville.nyc/events", headers=get_headers(), timeout=30)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Wonderville uses Squarespace - look for event items
        for item in soup.find_all('article') + soup.find_all('div', class_=re.compile(r'event|summary')):
            title_elem = item.find(['h1', 'h2', 'h3', 'a'])
            if title_elem:
                title = title_elem.get_text(strip=True)
                if not title or title.lower() in ['wonderville', 'events']:
                    continue
                
                # Find date
                date_elem = item.find(class_=re.compile(r'date|time'))
                date_text = date_elem.get_text(strip=True) if date_elem else ""
                
                # Look for date in text
                text = item.get_text(' ', strip=True)
                date_match = re.search(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[,\s]*\d{1,2}', text)
                date_str = date_match.group(0) if date_match else date_text or "TBD"
                
                # Get link
                link = item.find('a', href=True)
                url = link['href'] if link else None
                if url and url.startswith('/'):
                    url = f"https://www.wonderville.nyc{url}"
                
                events.append(Event(
                    venue="Wonderville",
                    title=title[:100],  # Truncate long titles
                    date=date_str,
                    url=url
                ))
    except Exception as e:
        print(f"Error scraping Wonderville: {e}")
    return events

def scrape_brooklyn_bowl() -> list[Event]:
    """Scrape Brooklyn Bowl events"""
    events = []
    try:
        resp = requests.get("https://www.brooklynbowl.com/brooklyn/shows/all", headers=get_headers(), timeout=30)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Find event cards
        for card in soup.find_all(['article', 'div'], class_=re.compile(r'event|card|show')):
            # Look for show title in h3 or links
            title_elem = card.find(['h3', 'h2'])
            if not title_elem:
                continue
                
            title = title_elem.get_text(strip=True)
            if not title or title.lower() in ['brooklyn bowl', 'closed', 'family bowl', 'open for bowling!']:
                continue
            
            # Find date - typically in format "Fri Jan 16th"
            text = card.get_text(' ', strip=True)
            date_match = re.search(r'(Sun|Mon|Tue|Wed|Thu|Fri|Sat)\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}', text)
            date_str = date_match.group(0) if date_match else "TBD"
            
            # Get event link
            link = card.find('a', href=True)
            url = None
            if link:
                href = link.get('href', '')
                if '/events/detail/' in href:
                    url = f"https://www.brooklynbowl.com{href}" if href.startswith('/') else href
            
            events.append(Event(
                venue="Brooklyn Bowl",
                title=title,
                date=date_str,
                url=url
            ))
    except Exception as e:
        print(f"Error scraping Brooklyn Bowl: {e}")
    return events

def scrape_gold_sounds_dice() -> list[Event]:
    """Scrape Gold Sounds via DICE API (they use DICE for ticketing)"""
    events = []
    try:
        # DICE has a public-ish API, but we'll scrape their venue page
        resp = requests.get("https://dice.fm/venue/gold-sounds-y3qr", headers=get_headers(), timeout=30)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # DICE is heavily JS-rendered, but we can try to get basic info
        for item in soup.find_all(['article', 'div', 'a'], class_=re.compile(r'event|card')):
            text = item.get_text(' ', strip=True)
            if len(text) > 10:
                # Try to extract event info
                title_match = re.search(r'^([^|]+)', text)
                date_match = re.search(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}', text)
                
                if title_match:
                    events.append(Event(
                        venue="Gold Sounds",
                        title=title_match.group(1)[:80],
                        date=date_match.group(0) if date_match else "TBD",
                        url="https://dice.fm/venue/gold-sounds-y3qr"
                    ))
    except Exception as e:
        print(f"Error scraping Gold Sounds: {e}")
    
    # Fallback: scrape from alternative sources
    if not events:
        try:
            resp = requests.get("https://www.songkick.com/venues/3217618-gold-sounds-bar", headers=get_headers(), timeout=30)
            soup = BeautifulSoup(resp.text, 'html.parser')
            for item in soup.find_all(['li', 'div'], class_=re.compile(r'event')):
                title_elem = item.find(['a', 'strong', 'h3'])
                if title_elem:
                    events.append(Event(
                        venue="Gold Sounds",
                        title=title_elem.get_text(strip=True),
                        date="See Songkick",
                        url="https://www.songkick.com/venues/3217618-gold-sounds-bar"
                    ))
        except Exception as e:
            print(f"Error scraping Gold Sounds fallback: {e}")
    
    return events

def scrape_nowadays_ra() -> list[Event]:
    """Scrape Nowadays via Resident Advisor"""
    events = []
    try:
        # Nowadays uses RA for their calendar
        resp = requests.get("https://ra.co/clubs/105873", headers=get_headers(), timeout=30)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # RA is heavily JS-rendered, limited scraping possible
        for item in soup.find_all(['article', 'li', 'div'], class_=re.compile(r'event')):
            title_elem = item.find(['h3', 'a', 'span'])
            if title_elem:
                title = title_elem.get_text(strip=True)
                if title:
                    events.append(Event(
                        venue="Nowadays",
                        title=title,
                        date="See RA",
                        url="https://ra.co/clubs/105873"
                    ))
    except Exception as e:
        print(f"Error scraping Nowadays: {e}")
    return events

def scrape_brooklyn_paramount() -> list[Event]:
    """Scrape Brooklyn Paramount - uses LiveNation/Ticketmaster"""
    events = []
    try:
        resp = requests.get("https://www.brooklynparamount.com/shows", headers=get_headers(), timeout=30)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # This site is heavily JS rendered, but let's try
        for item in soup.find_all(['article', 'div'], class_=re.compile(r'event|show|card')):
            title_elem = item.find(['h2', 'h3', 'a'])
            if title_elem:
                title = title_elem.get_text(strip=True)
                if title:
                    events.append(Event(
                        venue="Brooklyn Paramount",
                        title=title,
                        date="See Website",
                        url="https://www.brooklynparamount.com/shows"
                    ))
    except Exception as e:
        print(f"Error scraping Brooklyn Paramount: {e}")
    return events

def write_new_events(events: list[Event]):
    """Write new events to output file"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open(OUTPUT_FILE, 'a') as f:
        f.write(f"\n{'='*60}\n")
        f.write(f"New Events Found - {timestamp}\n")
        f.write(f"{'='*60}\n\n")
        
        for event in events:
            f.write(f"🎵 {event.venue}\n")
            f.write(f"   {event.title}\n")
            f.write(f"   📅 {event.date}\n")
            if event.url:
                f.write(f"   🔗 {event.url}\n")
            f.write("\n")

def main():
    print(f"🎸 NYC Venue Tracker - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("="*50)
    
    # Load previously seen events
    seen_ids = load_seen_events()
    print(f"📚 Loaded {len(seen_ids)} previously seen events")
    
    all_events = []
    scrapers = [
        ("H0L0", scrape_h0l0),
        # ("Wonderville", scrape_wonderville),
        # ("Brooklyn Bowl", scrape_brooklyn_bowl),
        # ("Gold Sounds", scrape_gold_sounds_dice),
        # ("Nowadays", scrape_nowadays_ra),
        # ("Brooklyn Paramount", scrape_brooklyn_paramount),
    ]
    
    for name, scraper in scrapers:
        print(f"\n🔍 Checking {name}...", end=" ")
        try:
            events = scraper()
            all_events.extend(events)
            print(f"found {len(events)} events")
        except Exception as e:
            print(f"error: {e}")
        time.sleep(1)  # Be polite
    
    # Filter to only new events
    new_events = []
    for event in all_events:
        event_id = event.event_id()
        if event_id not in seen_ids:
            new_events.append(event)
            seen_ids.add(event_id)
    
    # Write results
    if new_events:
        write_new_events(new_events)
        print(f"\n✨ Found {len(new_events)} NEW events! Written to {OUTPUT_FILE}")
    else:
        print(f"\n😴 No new events found")
    
    # Save updated seen events
    save_seen_events(seen_ids)
    print(f"💾 Saved {len(seen_ids)} event IDs to {SEEN_EVENTS_FILE}")

if __name__ == "__main__":
    main()
