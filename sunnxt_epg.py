#!/usr/bin/env python3
"""
Sun NXT EPG Generator — Real Schedule Data
Source: mitthu786/tvepg (daily updated, via GitHub raw)

Usage:
    python3 sunnxt_epg.py                   # fetch & generate EPG
    python3 sunnxt_epg.py --output epg.xml
    python3 sunnxt_epg.py --gz              # also write .gz
    python3 sunnxt_epg.py --list-channels
"""

import argparse
import gzip
import os
import sys
import urllib.request
import xml.etree.ElementTree as ET
from xml.dom import minidom

# ── Upstream source ────────────────────────────────────────────
EPG_URL = "https://raw.githubusercontent.com/mitthu786/tvepg/main/epg.xml.gz"

# ── Sun NXT Channel Map  (real IDs from upstream EPG) ─────────
CHANNELS = {
    # Tamil ──────────────────────────────────────────────────
    "sun195491": {"name": "Sun TV HD (Dolby Vision)", "lang": "ta", "group": "Tamil",    "category": "Entertainment",
                  "icon": "https://sund-images.sunnxt.com/14020/300x300_9dd88de4-18ab-493b-98fe-6eb27e9cbf5e.jpg"},
    "sun194403": {"name": "Sun TV HD",                "lang": "ta", "group": "Tamil",    "category": "Entertainment",
                  "icon": "https://sund-images.sunnxt.com/14020/300x300_9dd88de4-18ab-493b-98fe-6eb27e9cbf5e.jpg"},
    "sun194408": {"name": "Sun TV",                   "lang": "ta", "group": "Tamil",    "category": "Entertainment",
                  "icon": "https://sund-images.sunnxt.com/9016/300x300_4522d18b-56cc-42be-8365-c54e21a6e394.jpg"},
    "sun194405": {"name": "KTV HD",                   "lang": "ta", "group": "Tamil",    "category": "Movies",
                  "icon": "https://sund-images.sunnxt.com/26566/300x300_45814266-8c8b-45c6-a801-643e6734f73d.jpg"},
    "sun194409": {"name": "KTV",                      "lang": "ta", "group": "Tamil",    "category": "Movies",
                  "icon": "https://sund-images.sunnxt.com/32138/300x300_84b30aac-654e-4dd5-b5ee-bd8204254735.jpg"},
    "sun194406": {"name": "Sun Music HD",             "lang": "ta", "group": "Tamil",    "category": "Music",
                  "icon": "https://sund-images.sunnxt.com/9013/300x300_ff49d176-a9d2-4f50-b6bc-a10caac8d3a5.jpg"},
    "sun194410": {"name": "Sun Music",                "lang": "ta", "group": "Tamil",    "category": "Music",
                  "icon": "https://sund-images.sunnxt.com/9025/300x300_c8897f06-b2c0-4856-9d81-02181b821cf7.jpg"},
    "sun194391": {"name": "Sun Life",                 "lang": "ta", "group": "Tamil",    "category": "Lifestyle",
                  "icon": "https://sund-images.sunnxt.com/26569/300x300_SunLife_26569_1e6604fc-2df9-4598-8f1c-dcbda46254ab.jpg"},
    "sun194404": {"name": "Sun News",                 "lang": "ta", "group": "Tamil",    "category": "News",
                  "icon": "https://sund-images.sunnxt.com/38926/300x300_SunNews_38926_5921657d-45b6-445e-9e26-f0cd67be9d39.jpg"},
    "sun194407": {"name": "Adithya TV",               "lang": "ta", "group": "Tamil",    "category": "Entertainment",
                  "icon": "https://sund-images.sunnxt.com/9023/300x300_30878292-a63e-4414-acbc-902c0afb4b9b.jpg"},
    "sun194390": {"name": "Chutti TV",                "lang": "ta", "group": "Tamil",    "category": "Kids",
                  "icon": "https://sund-images.sunnxt.com/26567/300x300_c103e59e-217e-44fd-a087-651fcf8e6278.jpg"},

    # Telugu ─────────────────────────────────────────────────
    "sun195490": {"name": "Gemini TV HD (Dolby Vision)", "lang": "te", "group": "Telugu",   "category": "Entertainment",
                  "icon": "https://sund-images.sunnxt.com/14019/300x300_72a28627-db58-4739-b61c-4e4208897aed.jpg"},
    "sun194392": {"name": "Gemini TV HD",             "lang": "te", "group": "Telugu",   "category": "Entertainment",
                  "icon": "https://sund-images.sunnxt.com/14019/300x300_72a28627-db58-4739-b61c-4e4208897aed.jpg"},
    "sun194396": {"name": "Gemini TV",                "lang": "te", "group": "Telugu",   "category": "Entertainment",
                  "icon": "https://sund-images.sunnxt.com/9017/300x300_66d46fd1-643f-429f-9e19-db603fa0e5e4.jpg"},
    "sun192537": {"name": "Gemini Movies HD",         "lang": "te", "group": "Telugu",   "category": "Movies",
                  "icon": "https://sund-images.sunnxt.com/26570/300x300_285efca5-02f3-40a1-8f8c-d913e8f6b989.jpg"},
    "sun194384": {"name": "Gemini Movies",            "lang": "te", "group": "Telugu",   "category": "Movies",
                  "icon": "https://sund-images.sunnxt.com/9015/300x300_a4023b29-e49b-4c98-9621-95b7e5c39a19.jpg"},
    "sun194393": {"name": "Gemini Music HD",          "lang": "te", "group": "Telugu",   "category": "Music",
                  "icon": "https://sund-images.sunnxt.com/26568/300x300_eaa4e437-cce0-4411-8e46-13640be94c55.jpg"},
    "sun194395": {"name": "Gemini Music",             "lang": "te", "group": "Telugu",   "category": "Music",
                  "icon": "https://sund-images.sunnxt.com/9026/300x300_4cca05ef-46eb-4076-af6b-a8fdc1b88a27.jpg"},
    "sun194394": {"name": "Gemini Comedy",            "lang": "te", "group": "Telugu",   "category": "Comedy",
                  "icon": "https://sund-images.sunnxt.com/9027/300x300_5cb5b903-f1a0-4590-bb90-8cfa529322e2.jpg"},
    "sun194337": {"name": "Gemini Life",              "lang": "te", "group": "Telugu",   "category": "Lifestyle",
                  "icon": "https://sund-images.sunnxt.com/26572/300x300_da07159f-fa9c-45d0-beb2-685bedc12e33.jpg"},
    "sun194346": {"name": "Kushi TV",                 "lang": "te", "group": "Telugu",   "category": "Kids",
                  "icon": "https://sund-images.sunnxt.com/26571/300x300_d0545f75-f99b-4375-8f42-6120c95fc55c.jpg"},
    "sun200729": {"name": "TV9 Telugu",               "lang": "te", "group": "Telugu",   "category": "News",
                  "icon": "https://sund-images.sunnxt.com/tv9-telugu.jpg"},

    # Malayalam ──────────────────────────────────────────────
    "sun195489": {"name": "Surya TV HD (Dolby Vision)","lang": "ml", "group": "Malayalam","category": "Entertainment",
                  "icon": "https://sund-images.sunnxt.com/26574/300x300_6ed3be47-b8bf-45ee-adf1-fb5ae9621e08.jpg"},
    "sun194397": {"name": "Surya TV HD",              "lang": "ml", "group": "Malayalam","category": "Entertainment",
                  "icon": "https://sund-images.sunnxt.com/26574/300x300_6ed3be47-b8bf-45ee-adf1-fb5ae9621e08.jpg"},
    "sun194398": {"name": "Surya TV",                 "lang": "ml", "group": "Malayalam","category": "Entertainment",
                  "icon": "https://sund-images.sunnxt.com/9018/300x300_c10cc678-9321-43f8-b717-16fa7913a6ba.jpg"},
    "sun194385": {"name": "Surya Movies",             "lang": "ml", "group": "Malayalam","category": "Movies",
                  "icon": "https://sund-images.sunnxt.com/9019/300x300_71ddcc0b-16e7-48e9-9998-aa023200f4bc.jpg"},
    "sun194338": {"name": "Surya Music",              "lang": "ml", "group": "Malayalam","category": "Music",
                  "icon": "https://sund-images.sunnxt.com/26575/300x300_a73efcfb-e350-491c-94e0-bd75f0d9d5f2.jpg"},
    "sun193251": {"name": "Surya Comedy",             "lang": "ml", "group": "Malayalam","category": "Comedy",
                  "icon": "https://sund-images.sunnxt.com/30835/300x300_143a4af4-2f02-4c9c-814b-af149e6a5a95.jpg"},
    "sun194348": {"name": "Kochu TV",                 "lang": "ml", "group": "Malayalam","category": "Kids",
                  "icon": "https://sund-images.sunnxt.com/26573/300x300_5787336f-08b9-480f-9c97-3db09999b558.jpg"},
    "sun202222": {"name": "24 News",                  "lang": "ml", "group": "Malayalam","category": "News",
                  "icon": "https://sund-images.sunnxt.com/24news.jpg"},

    # Kannada ────────────────────────────────────────────────
    "sun194411": {"name": "Udaya TV HD (Dolby Vision)","lang": "kn", "group": "Kannada",  "category": "Entertainment",
                  "icon": "https://sund-images.sunnxt.com/30846/300x300_efb20223-e677-49fd-985e-806e7b162c6b.jpg"},
    "sun194399": {"name": "Udaya TV HD",              "lang": "kn", "group": "Kannada",  "category": "Entertainment",
                  "icon": "https://sund-images.sunnxt.com/30846/300x300_efb20223-e677-49fd-985e-806e7b162c6b.jpg"},
    "sun193239": {"name": "Udaya TV",                 "lang": "kn", "group": "Kannada",  "category": "Entertainment",
                  "icon": "https://sund-images.sunnxt.com/9029/300x300_9f0bcf68-5025-43af-8e60-b83fea67215c.jpg"},
    "sun194386": {"name": "Udaya Movies",             "lang": "kn", "group": "Kannada",  "category": "Movies",
                  "icon": "https://sund-images.sunnxt.com/26576/300x300_4ad767d2-e5d7-45f2-a95a-ab99f56cc2bf.jpg"},
    "sun194401": {"name": "Udaya Music",              "lang": "kn", "group": "Kannada",  "category": "Music",
                  "icon": "https://sund-images.sunnxt.com/9022/300x300_d85b4dcc-ad0c-4a5b-84fd-6dd91dc585e2.jpg"},
    "sun194400": {"name": "Udaya Comedy",             "lang": "kn", "group": "Kannada",  "category": "Comedy",
                  "icon": "https://sund-images.sunnxt.com/9014/300x300_8a47fe5c-81a8-42a4-8a05-f168e6a3c868.jpg"},
    "sun194347": {"name": "Chintu TV",                "lang": "kn", "group": "Kannada",  "category": "Kids",
                  "icon": "https://sund-images.sunnxt.com/26577/300x300_4a0f4f2f-e317-4230-9fb6-6169ef66991d.jpg"},
    "sun200730": {"name": "TV9 Kannada",              "lang": "kn", "group": "Kannada",  "category": "News",
                  "icon": "https://sund-images.sunnxt.com/tv9-kannada.jpg"},
    "sun202221": {"name": "Public TV",                "lang": "kn", "group": "Kannada",  "category": "News",
                  "icon": "https://sund-images.sunnxt.com/public-tv.jpg"},

    # Hindi ──────────────────────────────────────────────────
    "sun194389": {"name": "Sun Neo HD",               "lang": "hi", "group": "Hindi",    "category": "Entertainment",
                  "icon": "https://sund-images.sunnxt.com/75116/300x300_sun-neo.jpg"},
    "sun200731": {"name": "TV9 Bharatvarsh",          "lang": "hi", "group": "Hindi",    "category": "News",
                  "icon": "https://sund-images.sunnxt.com/tv9-bharatvarsh.jpg"},
    "sun207724": {"name": "News9",                    "lang": "kn", "group": "Kannada",  "category": "News",
                  "icon": "https://sund-images.sunnxt.com/news9.jpg"},

    # Bengali ────────────────────────────────────────────────
    "sun194388": {"name": "Sun Bangla",               "lang": "bn", "group": "Bengali",  "category": "Entertainment",
                  "icon": "https://sund-images.sunnxt.com/75117/300x300_4b19b530-f0bb-4b26-a9de-f3cdd5f8be20.jpg"},

    # Marathi ────────────────────────────────────────────────
    "sun194387": {"name": "Sun Marathi",              "lang": "mr", "group": "Marathi",  "category": "Entertainment",
                  "icon": "https://sund-images.sunnxt.com/75118/300x300_sun-marathi.jpg"},
}

SUNNXT_IDS = set(CHANNELS.keys())


def fetch_epg(url: str) -> bytes:
    print(f"[↓] Fetching {url} ...")
    headers = {"User-Agent": "Mozilla/5.0 (sunnxt-epg/2.0)"}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=90) as resp:
        gz = resp.read()
    xml_bytes = gzip.decompress(gz)
    print(f"[✓] {len(gz)//1024} KB → {len(xml_bytes)//1024} KB uncompressed")
    return xml_bytes


def build_filtered_epg(xml_bytes: bytes) -> ET.Element:
    print("[*] Parsing XML ...")
    src = ET.fromstring(xml_bytes)

    out = ET.Element("tv")
    out.set("generator-info-name", "sunnxt-epg")
    out.set("generator-info-url", "https://github.com/yourusername/sunnxt-epg")
    out.set("source-info-name", "Sun NXT Live (via tvepg)")
    out.set("source-info-url", "https://www.sunnxt.com/live")

    # Channels
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
            icon = ET.SubElement(new_ch, "icon")
            icon.set("src", meta["icon"])
            url_el = ET.SubElement(new_ch, "url")
            url_el.text = "https://www.sunnxt.com/live"

    # Channels not in upstream — add metadata-only entry
    for cid in SUNNXT_IDS - found:
        meta = CHANNELS[cid]
        new_ch = ET.SubElement(out, "channel")
        new_ch.set("id", cid)
        dn = ET.SubElement(new_ch, "display-name")
        dn.set("lang", meta["lang"])
        dn.text = meta["name"]
        ET.SubElement(new_ch, "icon").set("src", meta["icon"])
        ET.SubElement(new_ch, "url").text = "https://www.sunnxt.com/live"

    # Programmes
    prog_count = 0
    for prog in src.findall("programme"):
        if prog.get("channel", "") in SUNNXT_IDS:
            out.append(prog)
            prog_count += 1

    print(f"[✓] Channels from upstream: {len(found)}/{len(SUNNXT_IDS)} | Programmes: {prog_count}")
    return out


def prettify(element: ET.Element) -> str:
    raw = ET.tostring(element, encoding="unicode")
    dom = minidom.parseString(raw)
    lines = dom.toprettyxml(indent="  ").split("\n")
    lines[0] = '<?xml version="1.0" encoding="UTF-8"?>'
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Sun NXT EPG — real schedule data")
    parser.add_argument("--output", default="sunnxt_epg.xml", help="Output file")
    parser.add_argument("--gz", action="store_true", help="Also write .gz")
    parser.add_argument("--list-channels", action="store_true")
    args = parser.parse_args()

    if args.list_channels:
        print(f"\n{'ID':<15} {'Name':<30} {'Group':<12} {'Category'}")
        print("─" * 75)
        for grp in ["Tamil","Telugu","Malayalam","Kannada","Hindi","Bengali","Marathi"]:
            first = True
            for cid, meta in CHANNELS.items():
                if meta["group"] == grp:
                    if first:
                        print(f"\n  ── {grp} ──")
                        first = False
                    print(f"  {cid:<15} {meta['name']:<30} {meta['category']}")
        print(f"\nTotal: {len(CHANNELS)} channels\n")
        return

    xml_bytes = fetch_epg(EPG_URL)
    root = build_filtered_epg(xml_bytes)
    xml_str = prettify(root)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(xml_str)
    print(f"[✓] Saved: {args.output}  ({os.path.getsize(args.output)//1024} KB)")

    if args.gz:
        gz_path = args.output + ".gz"
        with gzip.open(gz_path, "wb") as f:
            f.write(xml_str.encode("utf-8"))
        print(f"[✓] Saved (gz): {gz_path}  ({os.path.getsize(gz_path)//1024} KB)")


if __name__ == "__main__":
    main()
