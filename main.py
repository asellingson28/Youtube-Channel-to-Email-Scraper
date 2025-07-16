import json
import sqlite3
import requests
import time
import schedule
import smtplib
from email.mime.text import MIMEText
from xml.etree import ElementTree as ET

# === Load Config ===
try:
    with open('config.json') as f:
        config = json.load(f)
except FileNotFoundError:
    print("⚠️Make sure you rename your template file!")
with open('channels.json') as f:
    channels = json.load(f)

# === Set up SQLite database ===
conn = sqlite3.connect(config["database"])
cur = conn.cursor()
cur.execute('''
CREATE TABLE IF NOT EXISTS videos (
    channel_id TEXT,
    video_id TEXT,
    title TEXT,
    published TEXT,
    PRIMARY KEY (channel_id, video_id)
)
''')
conn.commit()

# === Email sending ===
def send_email(subject, html_body):
    email_cfg = config["email"]
    msg = MIMEText(html_body, 'html')
    msg['Subject'] = subject
    msg['From'] = email_cfg['from']
    msg['To'] = email_cfg['to']

    try:
        with smtplib.SMTP(email_cfg['smtp_server'], email_cfg['smtp_port']) as server:
            server.starttls()
            server.login(email_cfg['username'], email_cfg['password'])
            server.send_message(msg)
        print(f"✅ Email sent: {subject}")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

def fetch_latest(channel_id):
    url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    try:
        r = requests.get(url)
        r.raise_for_status()
        root = ET.fromstring(r.content)
        ns = {
            'yt': 'http://www.youtube.com/xml/schemas/2015',
            'atom': 'http://www.w3.org/2005/Atom'
        }
        # Grab *all* entries, not just the first one
        entries = root.findall('atom:entry', ns)
        for entry in entries:
            link = entry.find('atom:link', ns).attrib['href']
            # if it's a Short, skip it and keep looking
            if "/shorts/" in link:
                print(f"🚫 Skipped Short: {link}")
                continue

            # otherwise return this first non-Short
            return {
                'video_id': entry.find('yt:videoId', ns).text,
                'title': entry.find('atom:title', ns).text,
                'published': entry.find('atom:published', ns).text,
                'link': link
            }

        # if we fell out of the loop, everything was shorts (or no videos)
        print("ℹ️ No non-Short videos found in feed.")
        return None

    except Exception as e:
        print(f"❌ Error fetching feed for channel {channel_id}: {e}")
        return None


# === Check all channels ===
def check_channels():
    for ch in channels:
        latest = fetch_latest(ch['id'])
        if latest:
            cur.execute("SELECT 1 FROM videos WHERE channel_id=? AND video_id=?", (ch['id'], latest['video_id']))
            if not cur.fetchone():
                # New video found
                cur.execute("INSERT INTO videos (channel_id, video_id, title, published) VALUES (?, ?, ?, ?)",
                            (ch['id'], latest['video_id'], latest['title'], latest['published']))
                conn.commit()
                send_email(
                    subject=f"📺 New video from {ch['name']}: {latest['title']}",
                    html_body=f"""
                        <h2>{latest['title']}</h2>
                        <p><a href="{latest['link']}">Watch on YouTube</a></p>
                        <p><small>Published: {latest['published']}</small></p>
                    """
                )

# === Scheduler ===
schedule.every(config["poll_interval_minutes"]).minutes.do(check_channels)
print(f"📡 Monitoring {len(channels)} channel(s) every {config['poll_interval_minutes']} minutes...")
check_channels()  # Run immediately once

while True:
    schedule.run_pending()
    time.sleep(1)
