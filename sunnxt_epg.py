#!/usr/bin/env python3
"""
Sun NXT EPG Generator
Fetches directly from pwaapi.sunnxt.com/epg/v2/channelEPG/{channelId}
Supports --days 1..14 for multi-day EPG accumulation

Usage:
    python3 sunnxt_epg.py                  # today only
    python3 sunnxt_epg.py --days 7         # fetch 7 days
    python3 sunnxt_epg.py --days 14        # fetch 14 days
    python3 sunnxt_epg.py --output epg.xml
    python3 sunnxt_epg.py --gz
    python3 sunnxt_epg.py --list-channels
"""

import argparse
import gzip
import json
import os
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from xml.dom import minidom

# ── Sun NXT PWA API ───────────────────────────────────────────
BASE_URL = "https://pwaapi.sunnxt.com/epg/v2/channelEPG/{channel_id}"
PARAMS   = "date={date}&level=epgstatic&imageProfile=mdpi&count=100&startIndex=1&orderBy=siblingOrder&orderMode=1"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Origin": "https://www.sunnxt.com",
    "Referer": "https://www.sunnxt.com/live",
}

# ── Sun NXT Channels ──────────────────────────────────────────
# channel_id = the numeric ID used in pwaapi URL
CHANNELS = [
    # Tamil ──────────────────────────────────────────────────
    {"id": "195491", "tvg_id": "sun195491", "name": "Sun TV HD (Dolby Vision)", "lang": "ta", "group": "Sun NXT Tamil",
     "icon": "https://sund-images.sunnxt.com/14020/300x300_9dd88de4-18ab-493b-98fe-6eb27e9cbf5e.jpg"},
    {"id": "194403", "tvg_id": "sun194403", "name": "Sun TV HD",                "lang": "ta", "group": "Sun NXT Tamil",
     "icon": "https://sund-images.sunnxt.com/14020/300x300_9dd88de4-18ab-493b-98fe-6eb27e9cbf5e.jpg"},
    {"id": "194408", "tvg_id": "sun194408", "name": "Sun TV",                   "lang": "ta", "group": "Sun NXT Tamil",
     "icon": "https://sund-images.sunnxt.com/9016/300x300_4522d18b-56cc-42be-8365-c54e21a6e394.jpg"},
    {"id": "194405", "tvg_id": "sun194405", "name": "KTV HD",                   "lang": "ta", "group": "Sun NXT Tamil",
     "icon": "https://sund-images.sunnxt.com/26566/300x300_45814266-8c8b-45c6-a801-643e6734f73d.jpg"},
    {"id": "194409", "tvg_id": "sun194409", "name": "KTV",                      "lang": "ta", "group": "Sun NXT Tamil",
     "icon": "https://sund-images.sunnxt.com/32138/300x300_84b30aac-654e-4dd5-b5ee-bd8204254735.jpg"},
    {"id": "194406", "tvg_id": "sun194406", "name": "Sun Music HD",             "lang": "ta", "group": "Sun NXT Tamil",
     "icon": "https://sund-images.sunnxt.com/9013/300x300_ff49d176-a9d2-4f50-b6bc-a10caac8d3a5.jpg"},
    {"id": "194410", "tvg_id": "sun194410", "name": "Sun Music",                "lang": "ta", "group": "Sun NXT Tamil",
     "icon": "https://sund-images.sunnxt.com/9025/300x300_c8897f06-b2c0-4856-9d81-02181b821cf7.jpg"},
    {"id": "194391", "tvg_id": "sun194391", "name": "Sun Life",                 "lang": "ta", "group": "Sun NXT Tamil",
     "icon": "https://sund-images.sunnxt.com/26569/300x300_SunLife_26569_1e6604fc-2df9-4598-8f1c-dcbda46254ab.jpg"},
    {"id": "194404", "tvg_id": "sun194404", "name": "Sun News",                 "lang": "ta", "group": "Sun NXT Tamil",
     "icon": "https://sund-images.sunnxt.com/38926/300x300_SunNews_38926_5921657d-45b6-445e-9e26-f0cd67be9d39.jpg"},
    {"id": "194407", "tvg_id": "sun194407", "name": "Adithya TV",               "lang": "ta", "group": "Sun NXT Tamil",
     "icon": "https://sund-images.sunnxt.com/9023/300x300_30878292-a63e-4414-acbc-902c0afb4b9b.jpg"},
    {"id": "194390", "tvg_id": "sun194390", "name": "Chutti TV",                "lang": "ta", "group": "Sun NXT Tamil",
     "icon": "https://sund-images.sunnxt.com/26567/300x300_c103e59e-217e-44fd-a087-651fcf8e6278.jpg"},

    # Telugu ─────────────────────────────────────────────────
    {"id": "195490", "tvg_id": "sun195490", "name": "Gemini TV HD (Dolby Vision)", "lang": "te", "group": "Sun NXT Telugu",
     "icon": "https://sund-images.sunnxt.com/14019/300x300_72a28627-db58-4739-b61c-4e4208897aed.jpg"},
    {"id": "194392", "tvg_id": "sun194392", "name": "Gemini TV HD",             "lang": "te", "group": "Sun NXT Telugu",
     "icon": "https://sund-images.sunnxt.com/14019/300x300_72a28627-db58-4739-b61c-4e4208897aed.jpg"},
    {"id": "194396", "tvg_id": "sun194396", "name": "Gemini TV",                "lang": "te", "group": "Sun NXT Telugu",
     "icon": "https://sund-images.sunnxt.com/9017/300x300_66d46fd1-643f-429f-9e19-db603fa0e5e4.jpg"},
    {"id": "192537", "tvg_id": "sun192537", "name": "Gemini Movies HD",         "lang": "te", "group": "Sun NXT Telugu",
     "icon": "https://sund-images.sunnxt.com/26570/300x300_285efca5-02f3-40a1-8f8c-d913e8f6b989.jpg"},
    {"id": "194384", "tvg_id": "sun194384", "name": "Gemini Movies",            "lang": "te", "group": "Sun NXT Telugu",
     "icon": "https://sund-images.sunnxt.com/9015/300x300_a4023b29-e49b-4c98-9621-95b7e5c39a19.jpg"},
    {"id": "194393", "tvg_id": "sun194393", "name": "Gemini Music HD",          "lang": "te", "group": "Sun NXT Telugu",
     "icon": "https://sund-images.sunnxt.com/26568/300x300_eaa4e437-cce0-4411-8e46-13640be94c55.jpg"},
    {"id": "194395", "tvg_id": "sun194395", "name": "Gemini Music",             "lang": "te", "group": "Sun NXT Telugu",
     "icon": "https://sund-images.sunnxt.com/9026/300x300_4cca05ef-46eb-4076-af6b-a8fdc1b88a27.jpg"},
    {"id": "194394", "tvg_id": "sun194394", "name": "Gemini Comedy",            "lang": "te", "group": "Sun NXT Telugu",
     "icon": "https://sund-images.sunnxt.com/9027/300x300_5cb5b903-f1a0-4590-bb90-8cfa529322e2.jpg"},
    {"id": "194337", "tvg_id": "sun194337", "name": "Gemini Life",              "lang": "te", "group": "Sun NXT Telugu",
     "icon": "https://sund-images.sunnxt.com/26572/300x300_da07159f-fa9c-45d0-beb2-685bedc12e33.jpg"},
    {"id": "194346", "tvg_id": "sun194346", "name": "Kushi TV",                 "lang": "te", "group": "Sun NXT Telugu",
     "icon": "https://sund-images.sunnxt.com/26571/300x300_d0545f75-f99b-4375-8f42-6120c95fc55c.jpg"},
    {"id": "200729", "tvg_id": "sun200729", "name": "TV9 Telugu",               "lang": "te", "group": "Sun NXT Telugu",
     "icon": "https://sund-images.sunnxt.com/tv9-telugu.jpg"},

    # Malayalam ──────────────────────────────────────────────
    {"id": "195489", "tvg_id": "sun195489", "name": "Surya TV HD (Dolby Vision)", "lang": "ml", "group": "Sun NXT Malayalam",
     "icon": "https://sund-images.sunnxt.com/26574/300x300_6ed3be47-b8bf-45ee-adf1-fb5ae9621e08.jpg"},
    {"id": "194397", "tvg_id": "sun194397", "name": "Surya TV HD",              "lang": "ml", "group": "Sun NXT Malayalam",
     "icon": "https://sund-images.sunnxt.com/26574/300x300_6ed3be47-b8bf-45ee-adf1-fb5ae9621e08.jpg"},
    {"id": "194398", "tvg_id": "sun194398", "name": "Surya TV",                 "lang": "ml", "group": "Sun NXT Malayalam",
     "icon": "https://sund-images.sunnxt.com/9018/300x300_c10cc678-9321-43f8-b717-16fa7913a6ba.jpg"},
    {"id": "194385", "tvg_id": "sun194385", "name": "Surya Movies",             "lang": "ml", "group": "Sun NXT Malayalam",
     "icon": "https://sund-images.sunnxt.com/9019/300x300_71ddcc0b-16e7-48e9-9998-aa023200f4bc.jpg"},
    {"id": "194338", "tvg_id": "sun194338", "name": "Surya Music",              "lang": "ml", "group": "Sun NXT Malayalam",
     "icon": "https://sund-images.sunnxt.com/26575/300x300_a73efcfb-e350-491c-94e0-bd75f0d9d5f2.jpg"},
    {"id": "193251", "tvg_id": "sun193251", "name": "Surya Comedy",             "lang": "ml", "group": "Sun NXT Malayalam",
     "icon": "https://sund-images.sunnxt.com/30835/300x300_143a4af4-2f02-4c9c-814b-af149e6a5a95.jpg"},
    {"id": "194348", "tvg_id": "sun194348", "name": "Kochu TV",                 "lang": "ml", "group": "Sun NXT Malayalam",
     "icon": "https://sund-images.sunnxt.com/26573/300x300_5787336f-08b9-480f-9c97-3db09999b558.jpg"},
    {"id": "202222", "tvg_id": "sun202222", "name": "24 News",                  "lang": "ml", "group": "Sun NXT Malayalam",
     "icon": "https://sund-images.sunnxt.com/24news.jpg"},

    # Kannada ────────────────────────────────────────────────
    {"id": "194411", "tvg_id": "sun194411", "name": "Udaya TV HD (Dolby Vision)", "lang": "kn", "group": "Sun NXT Kannada",
     "icon": "https://sund-images.sunnxt.com/30846/300x300_efb20223-e677-49fd-985e-806e7b162c6b.jpg"},
    {"id": "194399", "tvg_id": "sun194399", "name": "Udaya TV HD",              "lang": "kn", "group": "Sun NXT Kannada",
     "icon": "https://sund-images.sunnxt.com/30846/300x300_efb20223-e677-49fd-985e-806e7b162c6b.jpg"},
    {"id": "193239", "tvg_id": "sun193239", "name": "Udaya TV",                 "lang": "kn", "group": "Sun NXT Kannada",
     "icon": "https://sund-images.sunnxt.com/9029/300x300_9f0bcf68-5025-43af-8e60-b83fea67215c.jpg"},
    {"id": "194386", "tvg_id": "sun194386", "name": "Udaya Movies",             "lang": "kn", "group": "Sun NXT Kannada",
     "icon": "https://sund-images.sunnxt.com/26576/300x300_4ad767d2-e5d7-45f2-a95a-ab99f56cc2bf.jpg"},
    {"id": "194401", "tvg_id": "sun194401", "name": "Udaya Music",              "lang": "kn", "group": "Sun NXT Kannada",
     "icon": "https://sund-images.sunnxt.com/9022/300x300_d85b4dcc-ad0c-4a5b-84fd-6dd91dc585e2.jpg"},
    {"id": "194400", "tvg_id": "sun194400", "name": "Udaya Comedy",             "lang": "kn", "group": "Sun NXT Kannada",
     "icon": "https://sund-images.sunnxt.com/9014/300x300_8a47fe5c-81a8-42a4-8a05-f168e6a3c868.jpg"},
    {"id": "194347", "tvg_id": "sun194347", "name": "Chintu TV",                "lang": "kn", "group": "Sun NXT Kannada",
     "icon": "https://sund-images.sunnxt.com/26577/300x300_4a0f4f2f-e317-4230-9fb6-6169ef66991d.jpg"},
    {"id": "200730", "tvg_id": "sun200730", "name": "TV9 Kannada",              "lang": "kn", "group": "Sun NXT Kannada",
     "icon": "https://sund-images.sunnxt.com/tv9-kannada.jpg"},
    {"id": "202221", "tvg_id": "sun202221", "name": "Public TV",                "lang": "kn", "group": "Sun NXT Kannada",
     "icon": "https://sund-images.sunnxt.com/public-tv.jpg"},
    {"id": "207724", "tvg_id": "sun207724", "name": "News9",                    "lang": "kn", "group": "Sun NXT Kannada",
     "icon": "https://sund-images.sunnxt.com/news9.jpg"},

    # Hindi ──────────────────────────────────────────────────
    {"id": "194389", "tvg_id": "sun194389", "name": "Sun Neo HD",               "lang": "hi", "group": "Sun NXT Hindi",
     "icon": "https://sund-images.sunnxt.com/75116/300x300_sun-neo.jpg"},
    {"id": "200731", "tvg_id": "sun200731", "name": "TV9 Bharatvarsh",          "lang": "hi", "group": "Sun NXT Hindi",
     "icon": "https://sund-images.sunnxt.com/tv9-bharatvarsh.jpg"},

    # Bengali ────────────────────────────────────────────────
    {"id": "194388", "tvg_id": "sun194388", "name": "Sun Bangla",               "lang": "bn", "group": "Sun NXT Bengali",
     "icon": "https://sund-images.sunnxt.com/75117/300x300_4b19b530-f0bb-4b26-a9de-f3cdd5f8be20.jpg"},

    # Marathi ────────────────────────────────────────────────
    {"id": "194387", "tvg_id": "sun194387", "name": "Sun Marathi",              "lang": "mr", "group": "Sun NXT Marathi",
     "icon": "https://sund-images.sunnxt.com/75118/300x300_sun-marathi.jpg"},
]


def fmt_xmltv_time(iso_str: str) -> str:
    """Convert ISO 8601 to XMLTV format: 20260620183000 +0530"""
    try:
        # Handle formats like "2026-06-20T18:30:00+05:30" or "2026-06-20T18:30:00"
        iso_str = iso_str.replace("Z", "+00:00")
        if "+" in iso_str[10:] or iso_str.endswith("-05:30"):
            # Has timezone
            dt_part = iso_str[:19]
            dt = datetime.strptime(dt_part, "%Y-%m-%dT%H:%M:%S")
        else:
            dt = datetime.strptime(iso_str[:19], "%Y-%m-%dT%H:%M:%S")
        return dt.strftime("%Y%m%d%H%M%S") + " +0530"
    except Exception:
        return iso_str


def fetch_channel_epg(channel_id: str, date_str: str) -> list:
    """Fetch EPG for one channel on one date from Sun NXT API."""
    url = BASE_URL.format(channel_id=channel_id) + "?" + PARAMS.format(date=date_str)
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        # Navigate JSON — adjust keys based on actual API response
        items = (
            data.get("data", {}).get("items", []) or
            data.get("items", []) or
            data.get("result", {}).get("items", []) or
            data.get("epgData", []) or
            data.get("epg", []) or
            []
        )
        return items
    except Exception as e:
        print(f"    [!] {channel_id} {date_str}: {e}", file=sys.stderr)
        return []


def build_epg(days: int = 1) -> ET.Element:
    today = datetime.now()
    dates = [(today + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days)]

    root = ET.Element("tv")
    root.set("generator-info-name", "sunnxt-epg")
    root.set("generator-info-url", "https://github.com/yourusername/sunnxt-epg")
    root.set("source-info-name", "Sun NXT")
    root.set("source-info-url", "https://www.sunnxt.com/live")

    # Channel entries
    for ch in CHANNELS:
        ch_el = ET.SubElement(root, "channel")
        ch_el.set("id", ch["tvg_id"])
        dn = ET.SubElement(ch_el, "display-name")
        dn.set("lang", ch["lang"])
        dn.text = ch["name"]
        icon = ET.SubElement(ch_el, "icon")
        icon.set("src", ch["icon"])
        url_el = ET.SubElement(ch_el, "url")
        url_el.text = "https://www.sunnxt.com/live"

    # Programme entries
    total_progs = 0
    for ch in CHANNELS:
        print(f"  [{ch['id']}] {ch['name']}")
        for date_str in dates:
            items = fetch_channel_epg(ch["id"], date_str)
            for item in items:
                # Try common field names
                title    = item.get("title") or item.get("episodeTitle") or item.get("name") or "Unknown"
                desc     = item.get("description") or item.get("synopsis") or item.get("desc") or ""
                start_raw = item.get("startTime") or item.get("start") or item.get("broadcastStartTime") or ""
                end_raw   = item.get("endTime")   or item.get("end")   or item.get("broadcastEndTime")   or ""

                if not start_raw or not end_raw:
                    continue

                prog = ET.SubElement(root, "programme")
                prog.set("start",   fmt_xmltv_time(start_raw))
                prog.set("stop",    fmt_xmltv_time(end_raw))
                prog.set("channel", ch["tvg_id"])

                t = ET.SubElement(prog, "title")
                t.set("lang", ch["lang"])
                t.text = title

                if desc:
                    d = ET.SubElement(prog, "desc")
                    d.set("lang", ch["lang"])
                    d.text = desc

                # Optional fields
                ep_num = item.get("episodeNumber") or item.get("episode")
                if ep_num:
                    en = ET.SubElement(prog, "episode-num")
                    en.set("system", "onscreen")
                    en.text = str(ep_num)

                img = item.get("imageUrl") or item.get("image") or item.get("thumbnail")
                if img:
                    ET.SubElement(prog, "icon").set("src", img)

                total_progs += 1
            time.sleep(0.1)  # polite delay

    print(f"\n[✓] Total programmes: {total_progs}")
    return root


def prettify(element: ET.Element) -> str:
    raw = ET.tostring(element, encoding="unicode")
    dom = minidom.parseString(raw)
    lines = dom.toprettyxml(indent="  ").split("\n")
    lines[0] = '<?xml version="1.0" encoding="UTF-8"?>'
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Sun NXT EPG — direct from pwaapi.sunnxt.com")
    parser.add_argument("--days",         type=int, default=1, help="Days to fetch (1-14, default: 1)")
    parser.add_argument("--output",       default="sunnxt_epg.xml")
    parser.add_argument("--gz",           action="store_true", help="Also save .gz")
    parser.add_argument("--list-channels",action="store_true")
    args = parser.parse_args()

    if args.list_channels:
        print(f"\n{'ID':<10} {'TVG-ID':<15} {'Name':<35} {'Group'}")
        print("─" * 80)
        for ch in CHANNELS:
            print(f"  {ch['id']:<10} {ch['tvg_id']:<15} {ch['name']:<35} {ch['group']}")
        print(f"\nTotal: {len(CHANNELS)} channels\n")
        return

    days = max(1, min(14, args.days))
    print(f"[*] Fetching {len(CHANNELS)} channels × {days} day(s) from pwaapi.sunnxt.com ...\n")

    root = build_epg(days=days)
    xml_str = prettify(root)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(xml_str)
    print(f"[✓] Saved: {args.output} ({os.path.getsize(args.output)//1024} KB)")

    if args.gz:
        gz_path = args.output + ".gz"
        with gzip.open(gz_path, "wb") as f:
            f.write(xml_str.encode())
        print(f"[✓] Saved: {gz_path} ({os.path.getsize(gz_path)//1024} KB)")


if __name__ == "__main__":
    main()
