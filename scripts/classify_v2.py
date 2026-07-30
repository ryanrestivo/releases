#!/usr/bin/env python3
"""Reclassify all 3,390 rows using refined classifier rules."""

import csv
import re

# Load target data + references
target_rows = []
with open('/Users/ryanrestivo/Sites/releases/nyt_urls_with_paragraphs_removed_duplicates.csv', newline='', encoding='utf-8') as f:
    target_raw = list(csv.DictReader(f))

ref1_data = {}  # title -> (Category, Type)
with open('/Users/ryanrestivo/Sites/releases/references/labeling_test.csv', newline='', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        ref1_data[r.get('Title','')] = (r.get('Category',''), r.get('Type',''))

print(f"Target to classify: {len(target_raw)}")
print(f"Reference labels loaded: {len(ref1_data)}")

# === Helper functions ===
def safe_lower(s):
    return re.sub(r'[&#0-9xX]+;', ' ', s.lower())

def clean_text(s):
    return re.sub(r'[&#0-9xX]+;', ' ', s.lower())[:4000]

# === Category classifier ===
def get_category(title, fulltext):
    tl = safe_lower(title)
    ft = clean_text(fulltext)
    
    # 1. Fact checks - very distinctive title pattern
    if re.search(r'fact[- ]?check', tl) or 'false claims about our' in tl:
        return 'fact check'
    
    # 2. Awards - look for specific keywords but avoid false positives  
    # Only "wins" is the problematic one - only use titles with clear award context
    title_award_words = re.findall(r'\b(?:pulitzer|emmy|webby|polk|^nlga|sopaa)\b', tl)
    if title_award_words:
        return 'award'
    
    # Also "wins" + specific award types in the same sentence/title
    wins_match = re.search(r'\bwins?\s+(\d+)', tl)
    if wins_match:
        # Look at surrounding text for context
        full_lower = clean_text(f"{title} {fulltext}")
        if any(kw in full_lower for kw in ['pulitzer', 'emmy', 'webby', 'polk']):
            return 'award'
    
    # 3. Features - celebrations/milestones  
    if re.search(r'(?:175th|anniversary|commemorat)', tl):
        return 'feature'
    
    # 4. Statements - NYT official positions on legal/gov issues
    if re.search(r'responds?\s+to\s+lawsuit', tl):
        return 'statement'
    if 'supporting a campaign about' in tl or 'campaign highlighting' in tl:
        return 'statement'
    
    # 5. Company updates - product/business announcements (NOT staff changes)
    # "The New York Times to..." pattern = company update
    if re.match(r'^[Tt]he\s+(?:new\s+)?york\s+times\s+(?:to\s+|has\s+|now\s+|will\s+)', tl):
        ft_lower = clean_text(fulltext)
        # Only if NOT about staff
        not_staff = 'joins' not in ft_lower and 'hired' not in ft_lower and 'appointed' not in ft_lower and 'named ' not in ft_lower
        if not_staff:
            return 'company update'
    
    # "Introducing" pattern
    if re.search(r'^[Ii]ntroduct', tl):
        ft_lower = clean_text(fulltext)
        not_staff = 'joins' not in ft_lower and 'hired' not in ft_lower and 'named ' not in ft_lower and 'appointed' not in ft_lower
        if not_staff:
            return 'company update'
    
    # "NYT Games" - company updates for games/puzzles
    if re.match(r'^[Nn]ew\s+York\s+[Tt]imes\s+[Gg]ames', tl):
        ft_lower = clean_text(fulltext)
        not_staff = 'joins' not in ft_lower and 'hired' not in ft_lower and 'named ' not in ft_lower
        if not_staff:
            return 'company update'
    
    # "The Athletic" - company updates for athletic platform changes
    if re.match(r'^[Tt]he\s+[Aa]thletic', tl):
        ft_lower = clean_text(fulltext)
        not_staff = 'joins' not in ft_lower and 'hired' not in ft_lower and 'named ' not in ft_lower
        if not_staff:
            return 'company update'
    
    # 6. Default: staff announcement (majority class in training data)
    return 'staff announcement'

# === Type classifier ===
def get_type(title, fulltext):
    tl = safe_lower(title)
    ft = clean_text(fulltext)
    
    # Athletic (title-based) - most specific
    if 'athletic' in tl:
        return 'the athletic'
    
    # Cooking (context-based)
    cooking_patterns = ['cooking hires', 'creative director', 'nyt cooking']
    if any(kw.lower() in clean_text(f"{ft} {fulltext}") for kw in cooking_patterns):
        return 'cooking'
    
    # Games (title or text signal)
    game_kw = ['wordle', 'crossword', 'connections', 'nyt games']
    if any(kw in tl for kw in game_kw):
        return 'games'
    if 'puzzle' in ft and ('wordle' in ft or 'crossword' in ft or 'connections' in ft or 'game' in ft):
        return 'games'
    
    # Opinion (title-based)
    if 'opinion' in tl or 'op-ed' in tl:
        return 'opinion'
    
    # Audio (title/text signal)
    audio_kw = ['the daily', 'hard fork', 'serial productions', 'sunday episodes']
    if any(kw in tl for kw in audio_kw):
        return 'audio'
    if re.search(r'daily.*podcast|hard\s+fork.*audio', ft):
        return 'audio'
    
    # Default by text analysis - look for newsroom indicators
    desk_indicators = ['desk', 'newsroom', 'editorial', 'correspondent', 'reporter']
    if any(ind in ft for ind in desk_indicators):
        return 'newsroom'
    
    # Very short/fulltext-only staff changes default to newsroom 
    # unless they involve cooking, audio (already caught above) etc
    if len(clean_text(fulltext)) < 300 and 'cooking' not in ft:
        return "other/don't know"
    
    return "other/don't know"

# === Controversial classifier ===
def get_controversial(title, fulltext):
    tl = safe_lower(title)
    full_clean = clean_text(f"{title} {fulltext}")
    
    # Direct legal signals
    if re.search(r'sues\s+|sued\s+by|responds?\s+to\s+lawsuit|eeoc', tl):
        return 'Y'
    if 'lawsuit' in full_clean or 'legal action' in full_clean:
        return 'Y'
    
    # Press freedom signals  
    if any(kw.lower() in full_clean for kw in ['press freedom threat', 'free press attack', 'independent reporting under pressure', 'threats to free press']):
        return 'Y'
    
    return 'N'

# === Relevant classifier ===
def get_relevant(title, fulltext):
    tl = safe_lower(title)
    full_clean = clean_text(f"{title} {fulltext}")
    
    # Controversy implies relevance (from ref2)
    if get_controversial(title, fulltext) == 'Y':
        return 'Y'
    
    # Executive/leadership in title = Relevant
    exec_keywords = ['ceo', 'editor in chief', 'deputy editor in chief', 's.v.p.', 
                     'senior vice president', 'publisher', 'managing editor']
    if any(kw in tl for kw in exec_keywords):
        return 'Y'
    
    # Executive names in text = Relevant
    if any(nm.lower() in full_clean for nm in ['meredith kopit leven', 'ag sulzberger']):
        return 'Y'
    
    if any(pattern.lower() in full_clean for pattern in ['editor-in-chief', 'managing editor',
                                                           'deputy editor', 'chief executive officer',
                                                           's.v.p.', 'senior vice president, global security']):
        return 'Y'
    
    # Strategic announcements = Relevant
    strategy_patterns = ['core team vision', 'future of journalism', 'core mission']
    if any(p.lower() in full_clean for p in strategy_patterns):
        return 'Y'
    
    return 'N'

# === FULL CLASSIFICATION across all 3,390 rows ===
print(f"\n=== CLASSIFYING ALL {len(target_raw)} ROWS ===\n")

cat_counts = {}
type_counts = {}
cont_counts = {'Y': 0, 'N': 0}
rel_counts = {'Y': 0, 'N': 0}
unmatched_title_ref1 = set()
output_rows = []

for i, row in enumerate(target_raw):
    title   = row.get('storyTitle', '')
    fulltxt = row.get('fullText', '')
    
    cat     = get_category(title, fulltxt)
    typ     = get_type(title, fulltxt)
    cont    = get_controversial(title, fulltxt)
    rel     = get_relevant(title, fulltxt)
    
    # Track category distribution
    cat_counts[cat] = cat_counts.get(cat, 0) + 1
    type_counts[typ] = type_counts.get(typ, 0) + 1
    cont_counts[cont] += 1
    rel_counts[rel] += 1
    
    output_rows.append({
        **row,
        'Category': cat,
        'Type': typ,
        'Controversial (Y/N)': cont,
        'Relevant (Y/N)': rel,
    })
    
    if (i + 1) % 500 == 0:
        print(f"  Processed {i+1}/{len(target_raw)} rows...")

# === Cross-reference with REF2 URL for C/R override ===
print("\nCross-referencing with REG2 (C/R flags by URL)...")
reg2_ref = {}
with open('/Users/ryanrestivo/Sites/releases/references/releases_labeling.csv', newline='', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        src = re.sub(r'[^a-z0-9\s\-/.]', '', (r.get('Source URL','')).strip().lower()).replace(' ','')
        reg2_ref[src] = (
            r.get('Controversial (Y/N)','').strip().upper() or 'N',
            r.get('Relevant (Y/N)','').strip().upper()   or 'N'
        )

# Also merge REF1 title-to-cat/type into cross-ref 
ref1_cross = {}
with open('/Users/ryanrestivo/Sites/releases/references/labeling_test.csv', newline='', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        ref1_cross[r.get('Article Number','')] = (
            r.get('Category','').strip(), 
            r.get('Type','').strip()
        )

# Apply C/R overrides from REG2 where URL matches
c_from_reg2, t_from_ref1 = 0, 0
for i, row in enumerate(output_rows):
    url_norm = re.sub(r'[^a-z0-9\s\-/.]', '', (row.get('urls','')).strip().lower()).replace(' ','').rstrip('/')
    
    # If REG2 has a C/R match for this URL, use it 
    if url_norm in reg2_ref:
        co, rv = reg2_ref[url_norm]
        row['Controversial (Y/N)'] = co if co else 'N'  # use REG2 value when available
        row['Relevant (Y/N)']      = rv if rv else 'N'
        c_from_reg2 += 1
    
    # If REF1 has a Category/Type for this Article Number, override our classification
    artnum = ''
    src_url = (row.get('urls','') or '')
    if src_url:
        # Extract article number from URL path if possible 
        parts = src_url.split('/')
        for p in reversed(parts):
            if p.replace('-','').isdigit():
                artnum = p
                break
    
    if artnum and artnum in ref1_cross:
        c_from_ref1 += 1

# Fix the counting bug above - recount properly 
cat_counts, type_counts, cont_counts, rel_counts = {}, {}, {'Y':0,'N':0}, {'Y':0,'N':0}
for r in output_rows:
    cat_counts[r['Category']] = cat_counts.get(r['Category'], 0) + 1
    type_counts[r['Type']] = type_counts.get(r['Type'], 0) + 1
    cont_counts[r['Controversial (Y/N)']] += 1  
    rel_counts[r['Relevant (Y/N)']] += 1

# === Write output labeled CSV ===
out_path = '/Users/ryanrestivo/Sites/releases/nyt_urls_with_paragraphs_removed_duplicates_labeled.csv'
fieldnames = list(target_raw[0].keys()) + ['Category','Type','Controversial (Y/N)','Relevant (Y/N)']
with open(out_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(output_rows)

# === Print distribution summary ===
print(f"\n=== FINAL CLASSIFICATION SUMMARY ===")
print(f"Total rows processed: {len(output_rows)}")
print(f"\nCategory distribution:")
for c in sorted(cat_counts.keys(), key=lambda x: -cat_counts[x]):
    pct = cat_counts[c] / len(output_rows) * 100
    print(f"  {c:25s}: {cat_counts[c]:5d} ({pct:5.1f}%)")

print(f"\nType distribution:")
for t in sorted(type_counts.keys(), key=lambda x: -type_counts[x]):
    print(f"  {t:30s}: {type_counts[t]}")

print(f"\nControversial: {cont_counts}")
print(f"Relevant:      {rel_counts}")

print(f"\nOutput written to: {out_path}")
print("Done!")
