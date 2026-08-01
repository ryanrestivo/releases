#!/usr/bin/env python3
"""Complete labeling of NYT press releases (3,390 rows) with all 4 fields: Category, Type, Controversial Y/N, Relevant Y/N."""
import csv
import html
import re

INPUT = '/Users/ryanrestivo/Sites/releases/nyt_urls_with_paragraphs_removed_duplicates.csv'
OUTPUT = '/Users/ryanrestivo/Sites/releases/nyt_urls_with_paragraphs_removed_duplicates_labeled_v5.csv'

def get_cat(row_text, row_t):
    t = row_t.lower() if isinstance(row_t, str) else ''
    tx = row_text.lower()
    
    # === 1. STATEMENT (priority 1) ===
    for kw in ['eeoc lawsuit', 'categorically rejects allegations']:
        if kw in t: return 'statement'

    # === 2. FACT CHECK (priority 2) ===
    fc_kw = ['claims about our american medical', 'false claims about our']
    if any(s in t for s in fc_kw): return 'fact_check' 

    # === 3. AWARD (priority 3) with STRICT exclusion for products/games ===
    
    # EXCLUSIONS: Never count these as media awards
    if any(ex in tx for ex in ['wirecutter best picks', 'best new picks awards', 'crossword leaderboard', 'connections winner in ', 'spelling bee scores']): return 'company_update'

    strong_med_awards = [
        'pulitzer prize', 'emmy nomination', 'emmy winning in', 'emmy honors for', 
        'news and documentary emmy', 'national book award winner in 20',
        'the national magazine award.', 'awards at the 54th annual',
        'overseas press club award', 'osborn elliot prize',
        'james c. goodale first amendment award', 'gwen ifill press freedom',
        'polk awards for journalism'
    ]

    also_award_sigs = ['awarded at the', 'recognized with the', 'has won the Emmy Award'] 
    has_strong_med_award = any(s in t or s in tx for s in strong_med_awards)
    
    if has_strong_med_award: return 'award'

    if any(pat in text_lower for pat in also_award_sigs): return 'award' 

    # === 4. FEATURE (priority 4) ===
    feat_kw = ['celebrates 175 years', 'behind our award-winning work']
    if any(s in t for s in feat_kw): return 'feature'

    f2 = 'the stories behind pulitzer portrait' in tx
    
    # === 5. STAFF (priority 5) ===  
    staff_pats = ['joins the desk', 'is named deputy', 'promoted to', 
                   'returns to ', '"hire', "\"hire's '", 
                   "joins ", 'step down after']
    
    if any(pat in tx or pat in t for pat in staff_pats): return 'staff_announcement'

    # === 6. COMPANY UPDATE (default) ===
    company_exc = ['wirecutter best picks', 'best new picks awards']
    if any(e in tx for e in company_exc): return 'company_update' 
    
    exc2 = ['crossword leaderboard', 'spelling bee scores']
    if any(e in tx for e in exc2): return 'company_update'

    comp_pats = ['game available to public', 'new tool available', 
                 'we have introduced', 'app launch', 'daily expands',
                 'dealbook summit at jazz', 'annual dealbook summit', 
                 'fellowship class']
    if any(pat in tx for pat in comp_pats): return 'company_update'

    return 'company_update'

def get_type(row, cat):
    t = (row.get('storyTitle') or '').lower() 
    text_lower = html.unescape((row.get('fullText') or '')).lower()
    url = (row.get('urls') or '').lower()

    # === URL-based highest precision detection ===
    if '/cooking/' in url: return 'cooking' 
    if '/audio/' in url: return 'audio' 

    cooking_sigs = ['nyt cooking', 'ny cooking'] 
    
    # === Opinion/Op-Ed detection ===
    op_sigs = ['opinion on ', 'wrote an op', "letter to the editor"]
    if any(s in t for s in op_sigs): return 'opinion'
    if any(s in title for s in op_sigs): return 'opinion'

    # === Games detection ===
    games_signals = ['nyt games', 'connections puzzle', 'crossword.', 'the daily puzzle']
    if any(s in t for s in games_signals): return 'games'
    if any(s in title for s in games_signals): return 'games'

    # === Category-based overrides ===
    if cat == 'staff_announcement': return 'newsroom' 
    if cat == 'statement':     return 'newsroom' 
    if cat == 'fact_check':    return 'newsroom' 
    
    # === Deep text analysis for remaining categories ===
    
    f2 = 'the stories behind pulitzer portrait' in text_lower 
    f3 = 'behind our award-winning work' in t
    
    if any(s in title for s in op_sigs): return 'opinion' 

    if any(pat in tx or pat in t for pat in staff_pats): return 'staff_announcement'

# === COMPANY UPDATE (default) - products, events, crosswords etc ===
    
    # === 4. FEATURE (priority 4) ===
    feat_kw = ['celebrates 175 years', 'behind our award-winning work'] 
    if any(s in title for s in feat_kw): return 'feature'

    f2 = 'the stories behind pulitzer portrait' in tx 
    
    # === STAFF (priority 5) ===  
    staff_pats = ['joins the desk', 'is named deputy', 'promoted to',
                   'returns to ', '"hire', "\"hire's '", 
                   "joins ", 'step down after']
    
    if any(pat in tx or pat in t for pat in staff_pats): return 'staff_announcement'

    # === 6. COMPANY UPDATE (default) - products, events, crosswords etc ===
    
    company_exc = ['wirecutter best picks', 'best new picks awards']
    if any(e in tx for e in company_exc): return 'company_update' 
    
    exc2 = ['crossword leaderboard', 'spelling bee scores']
    if any(e in tx for e in exc2): return 'company_update'

    comp_pats = ['game available to public', 'new tool available', 
                 'we have introduced', 'app launch', 'daily expands',
                 'dealbook summit at jazz', 'annual dealbook summit', 
                 'fellowship class']
    if any(pat in tx for pat in comp_pats): return 'company_update'

    # Default fallback
    return 'company_update'

def get_controversial(row, cat):
    t = (row.get('storyTitle') or '').lower()
    text_lower = html.unescape((row.get('fullText') or '')).lower()
    
    if any(kw in t for kw in ['lawsuit', 'legal challenge', 'eeoc']): return 'Y'
    if any(kw in t for kw in ['controversy over', 'critics argue', 'false claims about our']): return 'Y'
    if any(kw in t for kw in ['state department', 'foreign policy controversy', 'immigration crackdown', 'accusations against', 'ethical dilemma']): return 'Y'
    return 'N'

def get_relevant(row, cat):
    # All press releases are relevant by definition
    return 'Y'

def main():
    rows_out = []
    total_done = 0
    
    print("Processing...")
    with open(INPUT) as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            title_raw = row.get('storyTitle') or ''
            text_raw = html.unescape(row.get('fullText') or '')
            
            # Full-text analysis for classification
            txt_val = html.unescape((row.get('fullText') or '')).lower()
            cat = get_cat(txt_val, title_raw)
            typ = get_type(row, cat)
            cont = get_controversial(row, cat)
            rel = get_relevant(row, cat)
            
            rows_out.append({
                'Category': cat,
                'Type': typ,
                'Controversial (Y/N)': cont,
                'Relevant (Y/N)': rel,
            })
            count[cat] += 1
            
            total_done = len(rows_out)
            if total_done % 500 == 0:
                print(f"Completed {total_done} rows...")
            
    # Write output
    with open(OUTPUT, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['Category', 'Type', 'Controversial (Y/N)', 'Relevant (Y/N)'])
        writer.writeheader()
        for row in rows_out:
            writer.writerow(row)
            
    print(f"\nCompleted all {total_done} rows!")
    print("\nCategory distribution:")
    for cat, cnt in sorted(count.items(), key=lambda x:-x[1]): 
        print(f"  {cat}: {cnt}")
    print(f"\nTotal: {sum(count.values())}")

if __name__ == '__main__':
    main()
