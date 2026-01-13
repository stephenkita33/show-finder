# NYC Concert Venue Tracker 🎸

A Python script that monitors your favorite NYC concert venues for new show announcements and writes them to a local file.

## Tracked Venues

**Queens:**
- H0L0 (Ridgewood)
- Nowadays (Ridgewood)

**Brooklyn:**
- Brooklyn Bowl
- Brooklyn Paramount
- Gold Sounds
- Wonderville

## Setup

1. **Install Python 3.9+** if you don't have it

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the tracker:**
   ```bash
   python venue_tracker.py
   ```

## Output

- **`new_events.txt`** - New events are appended here each time you run the script
- **`seen_events.json`** - Tracks which events you've already seen (for deduplication)

## Running Automatically

### macOS/Linux (cron)
Run every 6 hours:
```bash
crontab -e
# Add this line:
0 */6 * * * cd /path/to/venue_tracker && python venue_tracker.py
```

### macOS (launchd)
Create `~/Library/LaunchAgents/com.venue.tracker.plist`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.venue.tracker</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/path/to/venue_tracker.py</string>
    </array>
    <key>StartInterval</key>
    <integer>21600</integer>
    <key>WorkingDirectory</key>
    <string>/path/to/venue_tracker</string>
</dict>
</plist>
```
Then: `launchctl load ~/Library/LaunchAgents/com.venue.tracker.plist`

### Windows (Task Scheduler)
1. Open Task Scheduler
2. Create Basic Task → Run every 6 hours
3. Action: Start a Program → `python venue_tracker.py`

## Customization

### Adding More Venues

Edit `venue_tracker.py` and add a new scraper function:

```python
def scrape_new_venue() -> list[Event]:
    events = []
    # Your scraping logic here
    return events
```

Then add it to the `scrapers` list in `main()`.

### Changing Check Frequency

Adjust your cron/scheduler settings. For shows that sell out fast, every 1-2 hours is good. For casual monitoring, daily is fine.

## Notes

- **Rate limiting:** The script waits 1 second between venues to be polite
- **JS-heavy sites:** Some venues (Brooklyn Paramount, RA) render content with JavaScript, so scraping is limited. Consider using Selenium or Playwright for better results
- **API alternatives:** Check if venues have email newsletters - often the fastest way to hear about shows

## Troubleshooting

**"No events found"**
- Some sites block scrapers. Try adding a different User-Agent
- The site structure may have changed - check the HTML and update selectors

**"Connection errors"**
- Check your internet connection
- The site may be down

## Upgrading to Email/SMS Notifications

Want notifications instead of a file? Add one of these:

### Email (using Gmail)
```python
import smtplib
from email.mime.text import MIMEText

def send_email(events):
    msg = MIMEText("\n".join([f"{e.venue}: {e.title}" for e in events]))
    msg['Subject'] = f"🎵 {len(events)} new shows!"
    msg['From'] = 'you@gmail.com'
    msg['To'] = 'you@gmail.com'
    
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login('you@gmail.com', 'app-password')
        server.send_message(msg)
```

### Discord Webhook
```python
import requests

def send_discord(events):
    webhook_url = "YOUR_WEBHOOK_URL"
    content = "\n".join([f"**{e.venue}**: {e.title} ({e.date})" for e in events])
    requests.post(webhook_url, json={"content": f"🎵 New Shows!\n{content}"})
```

### Pushover (mobile push notifications)
```python
import requests

def send_pushover(events):
    requests.post("https://api.pushover.net/1/messages.json", data={
        "token": "YOUR_APP_TOKEN",
        "user": "YOUR_USER_KEY",
        "message": "\n".join([f"{e.venue}: {e.title}" for e in events]),
        "title": "New Shows!"
    })
```

---

Happy concert hunting! 🎶
