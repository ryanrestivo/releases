#!/usr/bin/env python3
"""Label all NYT release rows using v2 rules + references."""
import csv, re
from collections import defaultdict

TARGET    = "/Users/ryanrestivo/Sites/releases/nyt_urls_with_paragraphs_removed_duplicates.csv"
REF1_FILE = "/Users/ryanrestivo/Sites/releases/references/labeling_test.csv"
REF2_FILE = "/Users/ryanrestivo/Sites/releases/references/releases_labeling.csv"
OUTFILE   = "/Users/ryanrestivo/Sites/releases/nyt_urls_with_paragraphs_removed_duplicates_labeled_v4.csv"

def safe_lower(s):
    return re.sub(r"[&#][0-9xX]+;\\s*", " ", (s or "").lower())

def clean_text(s):
    return re.sub(r"[&#][0-9xX]+;", "", (s or ""))[:5000]

target_rows = list(csv.DictReader(open(TARGET, encoding="utf-8")))
ref1_data   = list(csv.DictReader(open(REF1_FILE, encoding="utf-8")))

print(f"Target: {len(target_rows)} | Ref1: {len(ref1_data)}")

def get_category(title, fulltext):
    tl = safe_lower(title)
    ft = clean_text(fulltext)
    if re.search(r"fact[- ]?check", tl) or "false claims about our" in tl:
        return "fact check"
    if re.findall(r"(?:pulitzer|emmy|webby|polk|nlga|sopaa)", tl):
        return "award"
    wins_m = re.search(r"\bwins?\s+(\d+)", tl)
    if wins_m and any(k in clean_text(f"{title} {fulltext}") for k in ["pulitzer","emmy","webby","polk"]):
        return "award"
    if re.search(r"(175th|anniversary|commemorat)", tl):
        return "feature"
    if re.search(r"responds?\s+to\s+lawsuit", tl):
        return "statement"
    if "campaign highlighting" in tl.lower():
        return "statement"
    if re.match(r"^the new york times to", tl):
        return "company update"
    if re.search(r"^introduct", tl) and "joins" not in safe_lower(fulltext):
        return "company update"
    if re.match(r"^new york times games", tl):
        return "company update"
    if re.match(r"^the athletic", tl) and "joins" not in safe_lower(clean_text(fulltext)):
        return "company update"
    return "staff announcement"

def get_type(title, fulltext):
    tl = safe_lower(title)
    ft = clean_text(f"{safe_lower(fulltext)}")
    if "athletic" in tl:
        return "the athletic"
    if any(kw in ft for kw in ["cooking hires","creative director","nyt cooking"]):
        return "cooking"
    game_kw = ["wordle","crossword","connections","nyt games"]
    if any(kw in tl for kw in game_kw):
        return "games"
    if re.search(r"puzzle.*word|crossword.*puzzle|connections.*game", ft):
        return "games"
    if "opinion" in tl or "op-ed" in tl:
        return "opinion"
    audio_kw = ["the daily","hard fork","serial productions","sunday episodes"]
    if any(kw in tl for kw in audio_kw):
        return "audio"
    desk = ["desk","newsroom","editorial","correspondent","reporter"]
    if any(ind in ft for ind in desk):
        return "newsroom"
    if len(safe_lower(fulltext)) < 300:
        return "other/don't know"
    return "other/don't know"

def get_controversial(title, fulltext):
    tl = safe_lower(title)
    fc = clean_text(f"{title} {fulltext}")
    if re.search(r"sues\s|sued by|responds? to lawsuit", tl):
        return "Y"
    if "lawsuit" in fc or "legal action" in fc:
        return "Y"
    for kw in ["press freedom threat","free press attack","independent reporting under pressure"]:
        if kw.lower() in fc:
            return "Y"
    for n in ["defense department","center for press freedom"]:
        if n.lower() in fc:
            return "Y"
    if re.search(r"deputy attorney general|civil rights", fc):
        return "Y"
    return "N"

def get_relevant(title, fulltext):
    tl = safe_lower(title)
    fc = clean_text(f"{title} {fulltext}")
    if get_controversial(title, fulltext) == "Y":
        return "Y"
    exec_kw = ["ceo","editor in chief","deputy editor","publisher",
                "managing editor","s.v.p.","senior vice president"]
    if any(kw in tl for kw in exec_kw):
        return "Y"
    for nm in ["meredith kopit levien","ag sulzberger"]:
        if nm.lower() in fc:
            return "Y"
    strats = ["core team vision","future of journalism","core mission"]
    if any(p in fc for p in strats):
        return "Y"
    if re.search(r"fellowship|diversity|inclusion", f"{tl} {fc}"):
        return "Y"
    return "N"