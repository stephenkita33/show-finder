import requests
import json

GRAPHQL_URL = "https://ra.co/graphql"
HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "Origin": "https://ra.co",
    "Referer": "https://ra.co/",
}

# Introspection query for Event fields
query = """
query {
  __type(name: "Event") {
    fields {
      name
    }
  }
}
"""

payload = {
    "query": query,
}

print("Introspecting Event fields...")
response = requests.post(GRAPHQL_URL, headers=HEADERS, json=payload)
print(f"Status Code: {response.status_code}")

try:
    data = response.json()
    fields = data.get("data", {}).get("__type", {}).get("fields", [])
    field_names = [f["name"] for f in fields]
    print("Event fields:", field_names)
except Exception as e:
    print(f"Failed to parse JSON: {e}")
    print(response.text[:1000])
