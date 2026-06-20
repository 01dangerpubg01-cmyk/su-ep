#!/usr/bin/env python3
"""
Sun NXT EPG (Electronic Program Guide) Generator
Generates XMLTV format EPG for Sun NXT live channels
Compatible with Jellyfin, Plex, Emby, TVHeadend, and other IPTV players

Usage:
    python sunnxt_epg.py                  # Generate EPG for today
    python sunnxt_epg.py --days 7         # Generate EPG for 7 days
    python sunnxt_epg.py --output epg.xml # Custom output file

GitHub: https://github.com/yourusername/sunnxt-epg
"""

import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime, timedelta
import argparse
import sys
import os

# ─────────────────────────────────────────────
# Sun NXT Channel Definitions
# Source: https://www.sunnxt.com/live
# ─────────────────────────────────────────────

CHANNELS = {
    # ── Tamil ────────────────────────────────
    "sunnxt-sun-tv-dv":        {"name": "Sun TV (Dolby Vision)",  "lang": "ta", "country": "IN", "category": "Entertainment", "icon": "https://www.sunnxt.com/images/channels/sun-tv.png"},
    "sunnxt-ktv-hd":           {"name": "KTV HD",                 "lang": "ta", "country": "IN", "category": "Movies",        "icon": "https://www.sunnxt.com/images/channels/ktv.png"},
    "sunnxt-sun-music-hd":     {"name": "Sun Music HD",           "lang": "ta", "country": "IN", "category": "Music",         "icon": "https://www.sunnxt.com/images/channels/sun-music.png"},
    "sunnxt-sun-life":         {"name": "Sun Life",               "lang": "ta", "country": "IN", "category": "Lifestyle",     "icon": "https://www.sunnxt.com/images/channels/sun-life.png"},
    "sunnxt-sun-news":         {"name": "Sun News",               "lang": "ta", "country": "IN", "category": "News",          "icon": "https://www.sunnxt.com/images/channels/sun-news.png"},
    "sunnxt-adithya-tv":       {"name": "Adithya TV",             "lang": "ta", "country": "IN", "category": "Entertainment", "icon": "https://www.sunnxt.com/images/channels/adithya-tv.png"},
    "sunnxt-chutti-tv":        {"name": "Chutti TV",              "lang": "ta", "country": "IN", "category": "Kids",          "icon": "https://www.sunnxt.com/images/channels/chutti-tv.png"},
    "sunnxt-sun-tv-sd":        {"name": "Sun TV SD",              "lang": "ta", "country": "IN", "category": "Entertainment", "icon": "https://www.sunnxt.com/images/channels/sun-tv.png"},
    "sunnxt-ktv-sd":           {"name": "KTV SD",                 "lang": "ta", "country": "IN", "category": "Movies",        "icon": "https://www.sunnxt.com/images/channels/ktv.png"},
    "sunnxt-sun-music-sd":     {"name": "Sun Music SD",           "lang": "ta", "country": "IN", "category": "Music",         "icon": "https://www.sunnxt.com/images/channels/sun-music.png"},

    # ── Telugu ───────────────────────────────
    "sunnxt-gemini-tv-dv":     {"name": "Gemini TV (Dolby Vision)", "lang": "te", "country": "IN", "category": "Entertainment", "icon": "https://www.sunnxt.com/images/channels/gemini-tv.png"},
    "sunnxt-gemini-tv-hd":     {"name": "Gemini TV HD",            "lang": "te", "country": "IN", "category": "Entertainment", "icon": "https://www.sunnxt.com/images/channels/gemini-tv.png"},
    "sunnxt-gemini-movies-hd": {"name": "Gemini Movies HD",        "lang": "te", "country": "IN", "category": "Movies",        "icon": "https://www.sunnxt.com/images/channels/gemini-movies.png"},
    "sunnxt-gemini-music-hd":  {"name": "Gemini Music HD",         "lang": "te", "country": "IN", "category": "Music",         "icon": "https://www.sunnxt.com/images/channels/gemini-music.png"},
    "sunnxt-gemini-comedy":    {"name": "Gemini Comedy",           "lang": "te", "country": "IN", "category": "Comedy",        "icon": "https://www.sunnxt.com/images/channels/gemini-comedy.png"},
    "sunnxt-gemini-life":      {"name": "Gemini Life",             "lang": "te", "country": "IN", "category": "Lifestyle",     "icon": "https://www.sunnxt.com/images/channels/gemini-life.png"},
    "sunnxt-kushi-tv":         {"name": "Kushi TV",               "lang": "te", "country": "IN", "category": "Kids",          "icon": "https://www.sunnxt.com/images/channels/kushi-tv.png"},
    "sunnxt-tv9-telugu":       {"name": "TV9 Telugu",             "lang": "te", "country": "IN", "category": "News",          "icon": "https://www.sunnxt.com/images/channels/tv9-telugu.png"},
    "sunnxt-gemini-tv-sd":     {"name": "Gemini TV SD",           "lang": "te", "country": "IN", "category": "Entertainment", "icon": "https://www.sunnxt.com/images/channels/gemini-tv.png"},
    "sunnxt-gemini-movies-sd": {"name": "Gemini Movies SD",       "lang": "te", "country": "IN", "category": "Movies",        "icon": "https://www.sunnxt.com/images/channels/gemini-movies.png"},
    "sunnxt-gemini-music-sd":  {"name": "Gemini Music SD",        "lang": "te", "country": "IN", "category": "Music",         "icon": "https://www.sunnxt.com/images/channels/gemini-music.png"},

    # ── Malayalam ────────────────────────────
    "sunnxt-surya-tv-hd":      {"name": "Surya TV HD",            "lang": "ml", "country": "IN", "category": "Entertainment", "icon": "https://www.sunnxt.com/images/channels/surya-tv.png"},
    "sunnxt-surya-movies":     {"name": "Surya Movies",           "lang": "ml", "country": "IN", "category": "Movies",        "icon": "https://www.sunnxt.com/images/channels/surya-movies.png"},
    "sunnxt-surya-music":      {"name": "Surya Music",            "lang": "ml", "country": "IN", "category": "Music",         "icon": "https://www.sunnxt.com/images/channels/surya-music.png"},
    "sunnxt-surya-comedy":     {"name": "Surya Comedy",           "lang": "ml", "country": "IN", "category": "Comedy",        "icon": "https://www.sunnxt.com/images/channels/surya-comedy.png"},
    "sunnxt-kochu-tv":         {"name": "Kochu TV",               "lang": "ml", "country": "IN", "category": "Kids",          "icon": "https://www.sunnxt.com/images/channels/kochu-tv.png"},
    "sunnxt-surya-tv-sd":      {"name": "Surya TV SD",            "lang": "ml", "country": "IN", "category": "Entertainment", "icon": "https://www.sunnxt.com/images/channels/surya-tv.png"},

    # ── Kannada ──────────────────────────────
    "sunnxt-udaya-tv-dv":      {"name": "Udaya TV (Dolby Vision)", "lang": "kn", "country": "IN", "category": "Entertainment", "icon": "https://www.sunnxt.com/images/channels/udaya-tv.png"},
    "sunnxt-udaya-tv-hd":      {"name": "Udaya TV HD",            "lang": "kn", "country": "IN", "category": "Entertainment", "icon": "https://www.sunnxt.com/images/channels/udaya-tv.png"},
    "sunnxt-udaya-movies":     {"name": "Udaya Movies",           "lang": "kn", "country": "IN", "category": "Movies",        "icon": "https://www.sunnxt.com/images/channels/udaya-movies.png"},
    "sunnxt-udaya-music":      {"name": "Udaya Music",            "lang": "kn", "country": "IN", "category": "Music",         "icon": "https://www.sunnxt.com/images/channels/udaya-music.png"},
    "sunnxt-udaya-comedy":     {"name": "Udaya Comedy",           "lang": "kn", "country": "IN", "category": "Comedy",        "icon": "https://www.sunnxt.com/images/channels/udaya-comedy.png"},
    "sunnxt-chintu-tv":        {"name": "Chintu TV",              "lang": "kn", "country": "IN", "category": "Kids",          "icon": "https://www.sunnxt.com/images/channels/chintu-tv.png"},
    "sunnxt-tv9-kannada":      {"name": "TV9 Kannada",            "lang": "kn", "country": "IN", "category": "News",          "icon": "https://www.sunnxt.com/images/channels/tv9-kannada.png"},
    "sunnxt-udaya-tv-sd":      {"name": "Udaya TV SD",            "lang": "kn", "country": "IN", "category": "Entertainment", "icon": "https://www.sunnxt.com/images/channels/udaya-tv.png"},

    # ── Hindi ────────────────────────────────
    "sunnxt-sun-neo":          {"name": "Sun Neo",                "lang": "hi", "country": "IN", "category": "Entertainment", "icon": "https://www.sunnxt.com/images/channels/sun-neo.png"},
    "sunnxt-tv9-bharatvarsh":  {"name": "TV9 Bharatvarsh",        "lang": "hi", "country": "IN", "category": "News",          "icon": "https://www.sunnxt.com/images/channels/tv9-bharatvarsh.png"},

    # ── Bengali ──────────────────────────────
    "sunnxt-sun-bangla":       {"name": "Sun Bangla",             "lang": "bn", "country": "IN", "category": "Entertainment", "icon": "https://www.sunnxt.com/images/channels/sun-bangla.png"},

    # ── Marathi ──────────────────────────────
    "sunnxt-sun-marathi":      {"name": "Sun Marathi",            "lang": "mr", "country": "IN", "category": "Entertainment", "icon": "https://www.sunnxt.com/images/channels/sun-marathi.png"},
}

# ─────────────────────────────────────────────
# Generic programme schedule per category
# (Replace with real API data if available)
# ─────────────────────────────────────────────

SCHEDULE_TEMPLATES = {
    "Entertainment": [
        ("00:00", "06:00", "Night Repeat"),
        ("06:00", "09:00", "Morning Shows"),
        ("09:00", "12:00", "Morning Serials"),
        ("12:00", "14:00", "Afternoon Movies"),
        ("14:00", "17:00", "Afternoon Serials"),
        ("17:00", "20:00", "Prime Time Serials"),
        ("20:00", "22:00", "Prime Time Specials"),
        ("22:00", "24:00", "Night Shows"),
    ],
    "Movies": [
        ("00:00", "03:00", "Late Night Movie"),
        ("03:00", "06:00", "Early Morning Movie"),
        ("06:00", "09:00", "Morning Movie"),
        ("09:00", "12:00", "Forenoon Movie"),
        ("12:00", "15:00", "Afternoon Movie"),
        ("15:00", "18:00", "Evening Movie"),
        ("18:00", "21:00", "Prime Time Movie"),
        ("21:00", "24:00", "Night Movie"),
    ],
    "Music": [
        ("00:00", "06:00", "Night Beats"),
        ("06:00", "10:00", "Morning Melodies"),
        ("10:00", "14:00", "Hit Parade"),
        ("14:00", "18:00", "Afternoon Hits"),
        ("18:00", "22:00", "Evening Chartbusters"),
        ("22:00", "24:00", "Night Grooves"),
    ],
    "News": [
        ("00:00", "06:00", "Night Bulletin"),
        ("06:00", "09:00", "Morning Headlines"),
        ("09:00", "12:00", "News at Nine"),
        ("12:00", "15:00", "Midday Report"),
        ("15:00", "18:00", "Afternoon News"),
        ("18:00", "21:00", "Evening News"),
        ("21:00", "23:00", "Prime Time News"),
        ("23:00", "24:00", "Late Night Bulletin"),
    ],
    "Kids": [
        ("00:00", "06:00", "Sleep Time"),
        ("06:00", "09:00", "Morning Cartoons"),
        ("09:00", "12:00", "Toons Hour"),
        ("12:00", "15:00", "Afternoon Adventures"),
        ("15:00", "18:00", "School Hour"),
        ("18:00", "21:00", "Family Time"),
        ("21:00", "24:00", "Good Night Stories"),
    ],
    "Comedy": [
        ("00:00", "06:00", "Repeat Comedy"),
        ("06:00", "10:00", "Morning Laughs"),
        ("10:00", "14:00", "Comedy Carnival"),
        ("14:00", "18:00", "Afternoon Giggles"),
        ("18:00", "22:00", "Prime Comedy"),
        ("22:00", "24:00", "Late Night Comedy"),
    ],
    "Lifestyle": [
        ("00:00", "06:00", "Repeat Shows"),
        ("06:00", "10:00", "Morning Lifestyle"),
        ("10:00", "14:00", "Health & Home"),
        ("14:00", "18:00", "Afternoon Features"),
        ("18:00", "22:00", "Prime Lifestyle"),
        ("22:00", "24:00", "Night Features"),
    ],
}


def fmt_time(dt: datetime) -> str:
    """Format datetime to XMLTV timestamp: YYYYMMDDHHMMSS +0530"""
    return dt.strftime("%Y%m%d%H%M%S") + " +0530"


def parse_time(base_date: datetime, time_str: str) -> datetime:
    """Parse HH:MM string relative to base_date. Handles '24:00' as next day 00:00."""
    h, m = map(int, time_str.split(":"))
    if h == 24:
        return (base_date + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return base_date.replace(hour=h, minute=m, second=0, microsecond=0)


def build_epg(days: int = 1) -> ET.Element:
    root = ET.Element("tv")
    root.set("generator-info-name", "sunnxt-epg")
    root.set("generator-info-url", "https://github.com/yourusername/sunnxt-epg")
    root.set("source-info-name", "Sun NXT")
    root.set("source-info-url", "https://www.sunnxt.com/live")

    # ── Channel entries ───────────────────────
    for ch_id, ch in CHANNELS.items():
        channel = ET.SubElement(root, "channel")
        channel.set("id", ch_id)

        display = ET.SubElement(channel, "display-name")
        display.set("lang", ch["lang"])
        display.text = ch["name"]

        if ch.get("icon"):
            icon = ET.SubElement(channel, "icon")
            icon.set("src", ch["icon"])

        url = ET.SubElement(channel, "url")
        url.text = "https://www.sunnxt.com/live"

    # ── Programme entries ─────────────────────
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    for day_offset in range(days):
        base_date = today + timedelta(days=day_offset)
        date_label = base_date.strftime("%d %b %Y")

        for ch_id, ch in CHANNELS.items():
            category = ch.get("category", "Entertainment")
            template = SCHEDULE_TEMPLATES.get(category, SCHEDULE_TEMPLATES["Entertainment"])

            for start_str, stop_str, title in template:
                start_dt = parse_time(base_date, start_str)
                stop_dt  = parse_time(base_date, stop_str)

                prog = ET.SubElement(root, "programme")
                prog.set("start",   fmt_time(start_dt))
                prog.set("stop",    fmt_time(stop_dt))
                prog.set("channel", ch_id)

                t = ET.SubElement(prog, "title")
                t.set("lang", ch["lang"])
                t.text = title

                desc = ET.SubElement(prog, "desc")
                desc.set("lang", ch["lang"])
                desc.text = f"{title} on {ch['name']} — {date_label}"

                cat = ET.SubElement(prog, "category")
                cat.set("lang", "en")
                cat.text = category

                country = ET.SubElement(prog, "country")
                country.text = ch["country"]

    return root


def prettify(element: ET.Element) -> str:
    raw = ET.tostring(element, encoding="unicode")
    dom = minidom.parseString(raw)
    return dom.toprettyxml(indent="  ", encoding=None)


def main():
    parser = argparse.ArgumentParser(
        description="Generate XMLTV EPG for Sun NXT live channels"
    )
    parser.add_argument(
        "--days", type=int, default=1,
        help="Number of days to generate EPG for (default: 1)"
    )
    parser.add_argument(
        "--output", type=str, default="sunnxt_epg.xml",
        help="Output XML file path (default: sunnxt_epg.xml)"
    )
    parser.add_argument(
        "--list-channels", action="store_true",
        help="List all channels and exit"
    )
    args = parser.parse_args()

    if args.list_channels:
        print(f"\n{'ID':<35} {'Name':<35} {'Lang':<6} {'Category'}")
        print("-" * 90)
        for ch_id, ch in CHANNELS.items():
            print(f"{ch_id:<35} {ch['name']:<35} {ch['lang']:<6} {ch['category']}")
        print(f"\nTotal: {len(CHANNELS)} channels")
        return

    print(f"[*] Generating EPG for {len(CHANNELS)} channels over {args.days} day(s)...")
    root = build_epg(days=args.days)

    xml_str = prettify(root)
    # Remove the extra XML declaration minidom adds when encoding=None
    lines = xml_str.split("\n")
    if lines[0].startswith("<?xml"):
        lines[0] = '<?xml version="1.0" encoding="UTF-8"?>'
    output = "\n".join(lines)

    out_path = args.output
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(output)

    size_kb = os.path.getsize(out_path) / 1024
    print(f"[✓] EPG saved to: {out_path}  ({size_kb:.1f} KB)")
    print(f"[✓] Channels: {len(CHANNELS)}  |  Days: {args.days}")


if __name__ == "__main__":
    main()
