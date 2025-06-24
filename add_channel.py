import json
import requests
import re
from bs4 import BeautifulSoup

def extract_channel_id(url_or_handle):
    if url_or_handle.startswith("@"):
        handle = url_or_handle
        url = f"https://www.youtube.com/{handle}"
    elif "youtube.com/" in url_or_handle and "/channel/" in url_or_handle:
        # already a direct channel link
        return url_or_handle.split("/channel/")[1].split("/")[0]
    elif "youtube.com/" in url_or_handle and "/@" in url_or_handle:
        url = url_or_handle
    else:
        print("❌ Please enter a valid handle (like @veritasium) or URL.")
        return None

    try:
        resp = requests.get(url)
        soup = BeautifulSoup(resp.text, 'html.parser')
        for tag in soup.find_all("link", {"rel": "canonical"}):
            match = re.search(r"/channel/([a-zA-Z0-9_-]+)", tag.get("href", ""))
            if match:
                return match.group(1)
    except Exception as e:
        print(f"⚠️ Error trying to fetch or parse the URL: {e}")

    return None

def add_channel():
    while True:
        user_input = input("Paste YouTube handle or URL (e.g. @veritasium or full URL): ").strip()
        name = input("What should we call this channel? (e.g. Veritasium): ").strip()

        channel_id = extract_channel_id(user_input)
        if not channel_id:
            print("❌ Could not extract channel ID. Try again?")
            if input("Y to retry, anything else to quit: ").strip().lower() != 'y':
                return
            continue

        try:
            with open("channels.json", "r") as f:
                channels = json.load(f)
        except FileNotFoundError:
            channels = []

        if any(ch['id'] == channel_id for ch in channels):
            print("⚠️ That channel already exists.")
            return

        channels.append({"id": channel_id, "name": name})
        with open("channels.json", "w") as f:
            json.dump(channels, f, indent=2)

        print(f"✅ Channel added: {name} ({channel_id})")
        break

if __name__ == "__main__":
    add_channel()
