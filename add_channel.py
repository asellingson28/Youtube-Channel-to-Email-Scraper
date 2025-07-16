import json
import os
import requests
import re
from bs4 import BeautifulSoup


def extract_channel_id(url_or_handle):
    """
    Extracts a YouTube channel ID from a handle (@handle),
    a full channel URL, or a handle URL.
    Returns None if it cannot be determined.
    """
    # Determine URL to fetch
    if url_or_handle.startswith("@"):
        url = f"https://www.youtube.com/{url_or_handle}"
    elif "youtube.com/" in url_or_handle and "/channel/" in url_or_handle:
        # Already a direct channel link
        return url_or_handle.split("/channel/")[1].split("/")[0]
    elif "youtube.com/" in url_or_handle and "/@" in url_or_handle:
        url = url_or_handle
    else:
        print("❌ Please enter a valid handle (like @veritasium) or URL.")
        return None

    try:
        resp = requests.get(url)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        # Look for the canonical link tag to find the /channel/{ID}
        canonical = soup.find("link", {"rel": "canonical"})
        if canonical and 'href' in canonical.attrs:
            match = re.search(r"/channel/([a-zA-Z0-9_-]+)", canonical['href'])
            if match:
                return match.group(1)
    except Exception as e:
        print(f"⚠️ Error fetching URL: {e}")

    return None


def load_channels():
    """Loads existing channels.json or returns empty list if not found/invalid."""
    if not os.path.exists("channels.json"):
        return []
    try:
        with open("channels.json", "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print("⚠️ channels.json is invalid JSON. Starting fresh.")
        return []


def save_channels(channels):
    """Writes the channels list back to channels.json."""
    with open("channels.json", "w") as f:
        json.dump(channels, f, indent=2)


def add_channel():
    channels = load_channels()

    while True:
        user_input = input("Paste YouTube handle or URL (e.g. @veritasium or full URL): ").strip()
        name = input("What should we call this channel? (e.g. Veritasium): ").strip()

        channel_id = extract_channel_id(user_input)
        if not channel_id:
            print("❌ Could not extract channel ID. Try again?")
            if input("Y to retry, anything else to quit: ").strip().lower() != 'y':
                return
            continue

        if any(ch['id'] == channel_id for ch in channels):
            print("⚠️ That channel already exists.")
            return

        channels.append({"id": channel_id, "name": name})
        save_channels(channels)
        print(f"✅ Channel added: {name} ({channel_id})")
        break


if __name__ == "__main__":
    add_channel()
