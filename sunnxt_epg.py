#!/usr/bin/env python3
"""
Sun NXT EPG Fetcher
Downloads EPG from mitthu786/tvepg, filters Sun NXT channels,
saves as sunnxt_epg.xml and sunnxt_epg.xml.gz

Usage:
    python3 sunnxt_epg.py
    python3 sunnxt_epg.py --output epg.xml
    python3 sunnxt_epg.py --gz
    python3 sunnxt_epg.py --list-channels
"""

import argparse
import gzip
import os
import urllib.request
import xml.etree.ElementTree as ET
from xml.dom import minidom

EPG_URL = "https://raw.githubusercontent.com/mitthu786/tvepg/main/epg.xml.gz"

CHANNELS = {
    # Tamil
    "sun195491": {"name": "Sun TV HD (Dolby Vision)", "lang": "ta", "group": "Tamil"},
    "sun194403": {"name": "Sun TV HD",                "lang": "ta", "group": "Tamil"},
    "sun194408": {"name": "Sun TV",                   "lang": "ta", "group": "Tamil"},
    "sun194405": {"name": "KTV HD",                   "lang": "ta", "group": "Tamil"},
    "sun194409": {"name": "KTV",                      "lang": "ta", "group": "Tamil"},
    "sun194406": {"name": "Sun Music HD",             "lang": "ta", "group": "Tamil"},
    "sun194410": {"name": "Sun Music",                "lang": "ta", "group": "Tamil"},
    "sun194391": {"name": "Sun Life",                 "lang": "ta", "group": "Tamil"},
    "sun194404": {"name": "Sun News",                 "lang": "ta", "group": "Tamil"},
    "sun194407": {"name": "Adithya TV",               "lang": "ta", "group": "Tamil"},
    "sun194390": {"name": "Chutti TV",                "lang": "ta", "group": "Tamil"},
    # Telugu
    "sun195490": {"name": "Gemini TV HD (Dolby Vision)", "lang": "te", "group": "Telugu"},
    "sun194392": {"name": "Gemini TV HD",             "lang": "te", "group": "Telugu"},
    "sun194396": {"name": "Gemini TV",                "lang": "te", "group": "Telugu"},
    "sun192537": {"name": "Gemini Movies HD",         "lang": "te", "group": "Telugu"},
    "sun194384": {"name": "Gemini Movies",            "lang": "te", "group": "Telugu"},
    "sun194393": {"name": "Gemini Music HD",          "lang": "te", "group": "Telugu"},
    "sun194395": {"name": "Gemini Music",             "lang": "te", "group": "Telugu"},
    "sun194394": {"name": "Gemini Comedy",            "lang": "te", "group": "Telugu"},
    "sun194337": {"name": "Gemini Life",              "lang": "te", "group": "Telugu"},
    "sun194346": {"name": "Kushi TV",                 "lang": "te", "group": "Telugu"},
    "sun200729": {"name": "TV9 Telugu",               "lang": "te", "group": "Telugu"},
    # Malayalam
    "sun195489": {"name": "Surya TV HD (Dolby Vision)","lang": "ml", "group": "Malayalam"},
    "sun194397": {"name": "Surya TV HD",              "lang": "ml", "group": "Malayalam"},
    "sun194398": {"name": "Surya TV",                 "lang": "ml", "group": "Malayalam"},
    "sun194385": {"name": "Surya Movies",             "lang": "ml", "group": "Malayalam"},
    "sun194338": {"name": "Surya Music",              "lang": "ml", "group": "Malayalam"},
    "sun193251": {"name": "Surya Comedy",             "lang": "ml", "group": "Malayalam"},
    "sun194348": {"name": "Kochu TV",                 "lang": "ml", "group": "Malayalam"},
    "sun202222": {"name": "24 News",                  "lang": "ml", "group": "Malayalam"},
    # Kannada
    "sun194411": {"name": "Udaya TV HD (Dolby Vision)","lang": "kn", "group": "Kannada"},
    "sun194399": {"name": "Udaya TV HD",              "lang": "kn", "group": "Kannada"},
    "sun193239": {"name": "Udaya TV",                 "lang": "kn", "group": "Kannada"},
    "sun194386": {"name": "Udaya Movies",             "lang": "kn", "group": "Kannada"},
    "sun194401": {"name": "Udaya Music",              "lang": "kn", "group": "Kannada"},
    "sun194400": {"name": "Udaya Comedy",             "lang": "kn", "group": "Kannada"},
    "sun194347": {"name": "Chintu TV",                "lang": "kn", "group": "Kannada"},
    "sun200730": {"name": "TV9 Kannada",              "lang": "kn", "group": "Kannada"},
    "sun202221": {"name": "Public TV",                "lang": "kn", "group": "Kannada"},
    "sun207724": {"name": "News9",                    "lang": "kn", "group": "Kannada"},
    # Hindi
    "sun194389": {"name": "Sun Neo HD",               "lang": "hi", "group": "Hindi"},
    "sun200731": {"name": "TV9 Bharatvarsh",          "lang": "hi", "group": "Hindi"},
    # Bengali
    "sun194388": {"name": "Sun Bangla",               "lang": "bn", "group": "Bengali"},
    # Marathi
    "sun194387": {"name": "Sun Marathi",              "lang": "mr", "group": "Marathi"},
}

SUNNXT_IDS = set(CHANNELS.keys())


def fetch_epg(url: str) -> bytes:
    print(f"[↓] Fetching {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (sunnxt-epg/2.0)"})
    with urllib.request.urlopen(req, timeout=90) as resp:
        gz = resp.read()
    xml_bytes = gzip.decompress(gz)
    print(f"[✓] {len(gz)//1024} KB gz → {len(xml_bytes)//1024} KB xml")
    return xml_bytes


def filter_epg(xml_bytes: bytes) -> ET.Element:
    print("[*] Parsing & filtering ...")
    src = ET.fromstring(xml_bytes)

    out = ET.Element("tv")
    out.set("generator-info-name", "sunnxt-epg")
    out.set("source-info-name", "Sun NXT")
    out.set("source-info-url", "https://www.sunnxt.com/live")

    found = set()
    for ch in src.findall("channel"):
        cid = ch.get("id", "")
        if cid in SUNNXT_IDS:
            found.add(cid)
            meta = CHANNELS[cid]
            new_ch = ET.SubElement(out, "channel")
            new_ch.set("id", cid)
            dn = ET.SubElement(new_ch, "display-name")
            dn.set("lang", meta["lang"])
            dn.text = meta["name"]

    prog_count = 0
    for prog in src.findall("programme"):
        if prog.get("channel", "") in SUNNXT_IDS:
            out.append(prog)
            prog_count += 1

    print(f"[✓] Channels: {len(found)}/{len(SUNNXT_IDS)} | Programmes: {prog_count}")
    return out


def prettify(element: ET.Element) -> str:
    raw = ET.tostring(element, encoding="unicode")
    dom = minidom.parseString(raw)
    lines = dom.toprettyxml(indent="  ").split("\n")
    lines[0] = '<?xml version="1.0" encoding="UTF-8"?>'
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Sun NXT EPG Fetcher")
    parser.add_argument("--output", default="sunnxt_epg.xml")
    parser.add_argument("--gz", action="store_true", help="Also save .gz")
    parser.add_argument("--list-channels", action="store_true")
    args = parser.parse_args()

    if args.list_channels:
        for grp in ["Tamil", "Telugu", "Malayalam", "Kannada", "Hindi", "Bengali", "Marathi"]:
            items = [(cid, m) for cid, m in CHANNELS.items() if m["group"] == grp]
            if items:
                print(f"\n── {grp} ──")
                for cid, m in items:
                    print(f"  {cid}  {m['name']}")
        print(f"\nTotal: {len(CHANNELS)} channels")
        return

    xml_bytes = fetch_epg(EPG_URL)
    root = filter_epg(xml_bytes)
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
