#!/usr/bin/env python3
"""Complete labeling pipeline for NYT press releases."""
import csv
import re
from collections import defaultdict


def norm(s):
    """Normalize string for comparison."""
    if not s:
        return ""
    cleaned = str(s).lower().strip()
    cleaned = re.sub(r"[^\w\s]", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def has_kw(text, keywords):
    """Check if any keyword appears in text (case insensitive)."""
    if not text:
        return False
    t = text.lower()
    for kw in keywords:
        if kw.lower() in t:
            return True
    return False


print("=" * 60)
print("LOADING DATA")
print("=" * 60)

# Load reference data (THE TRUTH - DO NOT MODIFY)
REF_CAT = {}
with open("/Users/ryanrestivo/Downloads/labeling_test.csv", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f, skipinitialspace=True)
    for row in reader:
        title = (row.get("Title") or "").strip()
        if not title:
            continue
        key = norm(title)
        cat_val = (row.get("Category") or "").strip()
        typ_val = (row.get("Type") or "").strip()
        REF_CAT[key] = {"cat": cat_val, "typ": typ_val}

REF_CR = {}
with open("/Users/ryanrestivo/Downloads/releases_labeling.csv", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f, skipinitialspace=True)
    for row in reader:
        title = (row.get("Title") or "").strip()
        if not title:
            continue
        key = norm(title)
        c_str = (row.get("Controversial (Y/N)") or "N").strip().upper()
        r_str = (row.get("Relevant (Y/N)") or "N").strip().upper()
        c_out = "Y" if c_str == "Y" else "N"
        r_out = "Y" if r_str == "Y" else "N"
        REF_CR[key] = {"c": c_out, "r": r_out}

# Load main CSV (3,390 rows to label)
with open(
    "/Users/ryanrestivo/Sites/releases/nyt_urls_with_paragraphs_removed_duplicates.csv",
    encoding="utf-8-sig",
) as f:
    MAIN = list(csv.DictReader(f))

print("Refs loaded: Cat.Type=%d C/R=%d" % (len(REF_CAT), len(REF_CR)))
print("Main rows to classify: %d\n" % len(MAIN))


# ============================================================  
# CLASSIFICATION ENGINE - learned from ref fullText pattern analysis
# ============================================================

def find_ref_match(story_norm):
    """Find exact reference match for a normalized story title."""
    for ref_t in REF_CAT:
        if story_norm == ref_t or (ref_t and (story_norm in ref_t or ref_t in story_norm)):
            return "cat", ref_t
    for ref_t in REF_CR:
        if story_norm == ref_t or (ref_t and (story_norm in ref_t or ref_t in story_norm)):
            return "cr", ref_t
    return None, None


def classify_row(story, fulltext):
    """Classify one NYT press release using taxonomy from reference patterns."""
    sn = norm(story) if story else ""
    ft = (fulltext or "").lower().replace("  ", " ")

    cat_val = ""
    typ_val = ""
    cont_val = "N"
    rel_val = "N"
    src_cat = "unmatched"
    src_typ = "unmatched"
    src_cv = "no_cr_match"
    src_rv = "no_rel_match"
    cr_matched = None  # Set if we find a C/R reference

    # STEP A: Try exact reference match first (THE TRUTH - never override)
    ref_type, ref_t = find_ref_match(sn)

    if ref_type == "cat":
        clb = REF_CAT[ref_t]
        cat_val = clb["cat"]
        src_cat = "exact_cat_" + ref_t[:50].replace(" ", "_")
        
        cr_matched = REF_CR.get(ref_t, None)
        if cr_matched:
            cont_val = cr_matched["c"]
            rel_val = cr_matched["r"]
            src_cv = "cr_Y" if cont_val == "Y" else "cr_N" + "_" + ref_t[:30].replace(" ", "_")
            src_rv = "rel_Y" if rel_val == "Y" else "rel_N" + "_" + ref_t[:30].replace(" ", "_")

    # STEP B: Apply learned patterns from analyzing labeled examples' fullText
    
    if not cat_val and not typ_val:  # No ref match - use learned patterns
        if has_kw(ft, ["joins", "joined", "new hire", "promoted"]):
            cat_val = "staff_announcement"
            src_cat = "pattern_staff_hire"
        
        if not cat_val and has_kw(ft, ["announces new partnership expansion launch"]):
            cat_val = "company_update"
            src_cat = "pattern_company_update"
            
        if not cat_val and has_kw(ft, ["celebrat anniversary special section featured"]):
            cat_val = "feature"
            src_cat = "pattern_feature"
            
        if not cat_val and has_kw(ft + sn, ["responds to lawsuit", "the new york times responds to"]):
            cont_val = "Y"
            rel_val = "Y"
            src_cv = "pattern_legal_controversy"
            src_rv = "pattern_high_relevance"
        
        if not cat_val and has_kw(ft, ["false claim", "inaccurate claims about our", "misreported"]):
            cont_val = "Y"  
            rel_val = "N"
            src_cv = "pattern_misinformation_controversial"
            src_rv = "pattern_factual_correction"

        if not cat_val and has_kw(ft, ["awards recognized won the award honored polk pulitzer"]):  
            cont_val = "N"
            rel_val = "Y"
            src_cv = "pattern_no_controversy"
            src_rv = "pattern_important_recognition"

    # Type classification using learned patterns from ref fullText analysis
    for ref_t2 in REF_CAT:
        clb2 = REF_CAT[ref_t]
        if sn == ref_t2 or (ref_t2 and (sn in ref_t2 or sf in sn)):
            typ_val = clb ["typ"]
            src_typ = "exact_type_" + ref_t [:50]. replace(" ", "_")
            
    # Default Type based on learned patterns
    for ref_t3 in REF_TYPE:
