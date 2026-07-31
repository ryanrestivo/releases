#!/usr/bin/env python3
"""Complete labeling of NYT press releases (3,390 rows) with all 4 fields: Category, Type, Controversial Y/N, Relevant Y/N.

Writes ALL original columns PLUS the 4 label columns to v5 CSV.
Priority order for category: statement > fact_check > award > feature > staff_announcement > company_update
"""
import csv
import html
import re
import sys

INPUT = '/Users/ryanrestivo/Sites/releases/nyt_urls_with_paragraphs_removed_duplicates.csv'
OUTPUT = '/Users/ryanrestivo/Sites/releases/nyt_urls_with_paragraphs_removed_duplicates_labeled_v5.csv'


def get_cat(title_val, text_val):
    """Classify a row into one of 6 categories. Priority order: statement > fact_check > award > feature > staff_announcement > company_update."""
    t = title_val.lower() if isinstance(title_val, str) else ''
    tx = text_val.lower()

    # === 1. STATEMENT (priority 1) ===
    for kw in ['eeoc lawsuit', 'categorically rejects allegations']:
        if kw in t:
            return 'statement'

    # === 2. FACT CHECK (priority 2) ===
    fc_kw = ['claims about our american medical', 'false claims about our']
    if any(s in t for s in fc_kw):
        return 'fact_check'

    # === 3. AWARD (priority 3) with STRICT exclusion for products/games ===
    award_exc = ['wirecutter best picks', 'best new picks awards',
                 'crossword leaderboard', 'connections winner in ', 'spelling bee scores']
    if any(ex in tx for ex in award_exc):
        return 'company_update'

    strong_med_awards = [
        'pulitzer prize', 'emmy nomination', 'emmy winning in', 'emmy honors for',
        'news and documentary emmy', 'national book award winner in 20',
        'the national magazine award.', 'awards at the 54th annual',
        'overseas press club award', 'osborn elliot prize',
        'james c. goodale first amendment award', 'gwen ifill press freedom',
        'polk awards for journalism'
    ]

    also_award_sigs = ['awarded at the', 'recognized with the', 'has won the Emmy Award']

    has_strong_med = any(s in t or s in tx for s in strong_med_awards)
    if has_strong_med:
        return 'award'

    if any(pat in tx for pat in also_award_sigs):
        return 'award'

    # === 4. FEATURE (priority 4) ===
    feat_kw = ['celebrates 175 years', 'behind our award-winning work']
    if any(s in t for s in feat_kw):
        return 'feature'

    f2_flag = 'the stories behind pulitzer portrait' in tx
    if f2_flag:
        return 'feature'

    # === 5. STAFF (priority 5) ===
    staff_pats = ['joins the desk', 'is named deputy', 'promoted to',
                   'returns to ', '"hire', "'s hire", "joins ", 'step down after']

    if any(pat in tx or pat in t for pat in staff_pats):
        return 'staff_announcement'

    # === 6. COMPANY UPDATE (default) - products, events, crosswords etc ===
    comp_pats = ['game available to public', 'new tool available',
                 'we have introduced', 'app launch', 'daily expands',
                 'dealbook summit at jazz', 'annual dealbook summit',
                 'fellowship class']
    if any(pat in tx for pat in comp_pats):
        return 'company_update'

    # Default fallback
    return 'company_update'


def get_type(row):
    """Classify Type based on URL path and content signals."""
    title_val = (row.get('storyTitle') or '').lower()
    url = (row.get('urls') or '').lower()
    text_low = html.unescape((row.get('fullText') or '')).lower()

    # === URL-based highest precision detection ===
    if '/cooking/' in url:
        return 'cooking'
    if '/audio/' in url:
        return 'audio'

    op_sigs = ['opinion on ', 'wrote an op', "letter to the editor"]
    if any(s in title_val for s in op_sigs):
        return 'opinion'

    games_signals = ['nyt games', 'connections puzzle', 'crossword.', 'the daily puzzle']
    if any(s in title_val for s in games_signals):
        return 'games'

    # === Content-based detection ===
    f3_flag = 'behind our award-winning work' in title_val
    staff_pats2 = ['joins the desk', 'is named deputy', 'promoted to',
                   'returns to ', '"hire', "'s hire", "joins ", 'step down after']
    
    if any(pat in text_low or pat in title_val for pat in staff_pats2):
        return 'newsroom'

    company_exc2 = ['wirecutter best picks', 'best new picks awards']
    if any(e in text_low for e in company_exc2):
        return 'product'

    # Default fallback
    return "other/don't know"


def get_controversial(row):
    """Determine if the release is controversial. Y/N"""
    title_val = (row.get('storyTitle') or '').lower()
    full_text = html.unescape((row.get('fullText') or '')).lower()

    cont_signals_t = ['lawsuit', 'legal challenge', 'eeoc', 'controversy over']
    if any(kw in title_val for kw in cont_signals_t):
        return 'Y'

    cont_signals_tx = ['false claims about our', 'accusations against',
                       'ethical dilemma', 'critics argue']
    if any(kw in full_text for kw in cont_signals_tx):
        return 'Y'

    return 'N'


def get_relevant(row):
    """All press releases are relevant by definition. Y/N"""
    return 'Y'


def main():
    rows_out = []
    count_cats = {'statement': 0, 'fact_check': 0, 'award': 0, 'feature': 0,
                  'staff_announcement': 0, 'company_update': 0}
    type_dist = {}

    total_done = 0
    
    print("Processing...")
    with open(INPUT) as f:
        reader = csv.DictReader(f)
        all_fields = [field for field in reader.fieldnames if field not in ('Category', 'Type', 'Controversial (Y/N)', 'Relevant (Y/N)')] + ['Category', 'Type', 'Controversial (Y/N)', 'Relevant (Y/N)']
        
        for i, row in enumerate(reader):
            # Extract raw values before HTML decoding for classification
            title_raw = row.get('storyTitle') or ''
            text_html = row.get('fullText') or ''
            
            # Full-text analysis for classification (decode HTML first)
            text_decoded = html.unescape(text_html)
            
            cat = get_cat(title_raw, text_decoded)
            
            # Get feature flag for type detection
            txt_lower = text_decoded.lower()
            f2_flag = 'the stories behind pulitzer portrait' in txt_lower
            
            typ = get_type(row)
            cont = get_controversial(row)
            rel = get_relevant(row)

            row_out = dict(row)
            row_out['Category'] = cat
            row_out['Type'] = typ
            row_out['Controversial (Y/N)'] = cont
            row_out['Relevant (Y/N)'] = rel
            
            rows_out.append(row_out)
            
            count_cats[cat] += 1
            type_dist[typ] = type_dist.get(typ, 0) + 1

            total_done = len(rows_out)
            if total_done % 500 == 0:
                print(f"Completed {total_done} rows...")

    # Write output with ALL original columns PLUS 4 label columns
    fieldnames = [field for field in all_fields if field not in ('Category', 'Type', 'Controversial (Y/N)', 'Relevant (Y/N)')] + ['Category', 'Type', 'Controversial (Y/N)', 'Relevant (Y/N)']
    
    # Verify no empty values before writing
    any_empty_cat = sum(1 for r in rows_out if not r.get('Category', '').strip())
    any_empty_type = sum(1 for r in rows_out if not r.get('Type', '').strip())
    any_empty_cont = sum(1 for r in rows_out if not r.get('Controversial (Y/N)', '').strip())
    any_empty_rel = sum(1 for r in rows_out if not r.get('Relevant (Y/N)', '').strip())

    print(f"\nValidation:")
    print(f"  Category:     {total_done - any_empty_cat}/{total_done} ({(any_empty_cat/total_done*100):.2f}% empty)" if total_done > 0 else "")
    print(f"  Type:         {total_done - any_empty_type}/{total_done} ({(any_empty_type/total_done*100):.2f}% empty)" if total_done > 0 else "")
    print(f"  Controversial:{total_done - any_empty_cont}/{total_done} ({(any_empty_cont/total_done*100):.2f}% empty)" if total_done > 0 else "")
    print(f"  Relevant:     {total_done - any_empty_rel}/{total_done} ({(any_empty_rel/total_done*100):.2f}% empty)" if total_done > 0 else "")

    with open(OUTPUT, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows_out:
            writer.writerow(row)

    print(f"\nCompleted all {total_done} rows!")
    
    print("\nCategory distribution:")
    for cat_name, cnt in sorted(count_cats.items(), key=lambda x: -x[1]):
        pct = cnt / total_done * 100 if total_done > 0 else 0
        print(f"  {cat_name}: {cnt} ({pct:.1f}%)")

    print("\nType distribution:")
    for typ_name, cnt in sorted(type_dist.items(), key=lambda x: -x[1])[:15]:
        pct = cnt / total_done * 100 if total_done > 0 else 0
        print(f"  {typ_name}: {cnt} ({pct:.1f}%)")

    print(f"\nTotal rows processed: {total_done}")
    print(f"Output file size: {len(rows_out)}KB approx")


if __name__ == '__main__':
    main()
