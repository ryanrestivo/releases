#!/usr/bin/env python3
"""
Complete labeling script for NYT press releases (3,390 rows).
Outputs: Category, Type, Controversial (Y/N), Relevant (Y/N)
based on reference data analysis and text signals.

Priority evaluation order (first match wins):
  statement > fact_check > award > feature > staff_announcement > company_update

Type determination is based on desk/source signals in the text title+body.
Controversial = Y when content involves political/administration attacks, immigration, EEOC lawsuits
Relevant = Y when content relates to NY-based operations or major national impact

Based on reference labeling of 81 samples + full-scan analysis of all 3,390 rows.
"""

import csv
import re
import html
import sys
from collections import Counter

# Load source data
SOURCE_PATH = '/Users/ryanrestivo/Sites/releases/nyt_urls_with_paragraphs_removed_duplicates.csv'
OUTPUT_PATH = '/Users/ryanrestivo/Sites/releases/nyt_urls_with_paragraphs_removed_duplicates_labeled_v4.csv'

def classify(row):
    url = row.get('urls', '')
    title_raw = row.get('storyTitle', '') or ''
    text_raw = html.unescape(row.get('fullText', '') or '')
    text_lower = text_raw.lower()
    title_lower = title_raw.lower()
    
    # --- CATEGORY CLASSIFICATION ---
    
    # 1. STATEMENT - official NYT response to political/legal issues
    if (any(w in text_lower for w in ['categorically rejects', 'rejects politically', 'responds to lawsuit', 
                                        'response to the eeoc', 'our position on immigration',
                                        'denies allegation', 'administration attacks'] +
               [text_lower.split('response to')[1].split('\n')[0][:30] if 'response to' in text_lower else '']) or
            any(w in title_lower for w in ['response to lawsuit', 'responds to eeoc', 'denies allegation'])):
        # Exclude fact checks from statement - fact checks come first priority 2
        category = 'statement'
    
    # 2. FACT CHECK - explicitly fact-checking content about NYT coverage
    elif (any(w in title_lower for w in ['fact-checking', 'fact-check']) or
          any(p in text_lower for p in ['false claims about our', 'claims about our',
                                         'our southern border', 'our coverage of the election'] +
              [w for w in ['false claims about our', 'claims about our',
                           'our coverage was inaccurate', 'we did not publish']]) or
          'false claims' in text_lower):
        category = 'fact_check'
    
    # 3. AWARD - NYT journalists won awards, honors, prizes
    # Must be actual award content NOT just words like "wins" in game context
    elif (any(w in title_lower for w in ['award', 'pulitzer', 'emmy', 'pulitzer prize', 
                                             'honored with', 'won ', 'winning', 'prize',
                                             'fellowship', 'national book award', 'pew grant']) or
          any(p in text_lower for p in ['has won the', 'was awarded the', 'received the award',
                                         'recognized with a', 'is honored with the', 
                                         'emmy award', 'pulitzer prize', 'national book',
                                         'osborn elliot', 'polk award', 'opc award',
                                         'gwen ifill press freedom', 'james c. goodale',
                                         'awarded by the', 'honor for excellence',
                                         'the times won', 'has been awarded',
                                         'recognized at the'] +
              [w for w in ['is honored with', 'has been honored']])):
        # EXCLUSION: game results, Wirecutter product reviews, crossword features
        # These contain "winning" or "award" but are NOT press releases about media awards
        if (any(w in text_lower for w in ['wirecutter best picks', 'connections puzzle', 
                                            'spelling bee scores', 'crossword leaderboard'])):
            category = 'company_update'
        else:
            # Verify it's actually an award by checking for award-specific signals
            award_signals = [w in text_lower for w in ['award', 'emmy', 'pulitzer', 'prize', 
                                                         'honor', 'honored', 'granted', 'bestowed']]
            if any(award_signals) or any(w in title_lower for w in ['award', 'pulitzer', 'emmy', 'pulitzer prize',
                                                                       'honored with', 'fellowship']):
                category = 'award'
    
    # 4. FEATURE - editorial content about the Times itself (e.g., 175th anniversary)
    elif (any(w in title_lower for w in ['celebrates 175 years', 'our story is', 
                                             'the stories behind', 'behind our award-winning']) or
          any(p in text_lower for p in ['times celebrates 175', 'stories behind the pulitzer'])):
        category = 'feature'
    
    # 5. STAFF - staff changes, hires, promotions, transfers, departures
    elif (any(w in title_lower for w in ['joins', 'hire', 'new role for', 'next chapter for', 
                                            'new deputy', 'nuevo editor', 'editor at large']) or
          any(p in text_lower for p in ['is now ', 'has been promoted to', 
                                          'will be an', 'joining the desk',
                                          'i am pleased to announce we have added',
                                          'is joining our team', 'we are delighted to announce',
                                          'welcoming', 'excited to share that',
                                          'i am excited to share with you',
                                          'are thrilled to welcome', 
                                          'has decided to step down',
                                          'will be an ', 'to join the']) or
          any(w in title_lower for w in ['new hire', 'new hires', 'new leader',
                                           'next paris bureau chief', 'new brazil bureau',
                                           'new deputy editor']) or
          any(p in text_lower for p in ['stepping down after']):
        category = 'staff_announcement'
    
    # 6. COMPANY UPDATE - everything else (product launches, events, podcasts, games, newsletters)
    else:
        category = 'company_update'
    
    # --- TYPE DETERMINATION ---
    type_val = determine_type(row, category)
    
    # --- CONTROVERSIAL DETERMINATION ---
    controversial = determine_controversial(title_raw, text_raw)
    
    # --- RELEVANT DETERMINATION ---  
    relevant = determine_relevant(url, title_raw, text_raw)
    
    return {
        'urls': url,
        'fullText': row.get('fullText', ''),
        'storyTitle': title_raw,
        'datePublished': row.get('datePublished', ''),
        'dateModified': row.get('dateModified', ''),
        'Category': category,
        'Type': type_val,
        'Controversial (Y/N)': controversial,
        'Relevant (Y/N)': relevant,
    }


def determine_type(row, category):
    """Determine Type based on desk/source signals in title and text."""
    url = row.get('urls', '').lower()
    title_lower = (row.get('storyTitle') or '').lower()
    text_lower = html.unescape(row.get('fullText') or '').lower()
    
    # Direct type identifiers from URL/slug
    if 'cooking' in url: return 'cooking'
    if 'athletic' in url and 'cookbook' not in title_lower: return 'the athletic'
    if 'audio' in url or any(w in text_lower for w in ['podcast episode', 'episode of the daily']): return 'audio'
    
    # Type from title/text patterns
    if category == 'company_update':
        if 'games' in text_lower or 'crossword' in text_lower or 'connections puzzle' in text_lower:
            return 'games'
        if 'cooking' in text_lower or 'kitchen kitchen' in text_lower:
            return 'cooking'
        if 'audio' in url or any(w in text_lower for w in ['podcast', 'audio series', 'daily episode']):
            return 'audio'
        if 'athletic' in text_lower and 'coverage' in text_lower:
            return 'the athletic'
            
    # Type from staff desk/location mentions
    if 'newsroom' in url or any(w in title_lower for w in ['new york', 'bureau chief', 'correspondent',
                                                              'editor at large', 'desk team',
                                                              'metro', 'business desk']):
        return 'newsroom'
        
    # Specific type signals from text
    if any(w in text_lower for w in ['opinion', 'op-ed', 'columnists', 'letter to the editor', 
                                        'wrote an op-ed']):
        return 'opinion'
    
    if 'cooking' in text_lower and 'recipe' in text_lower:
        return 'cooking'
        
    if any(w in url for w in ['cooking', 'recipe']):
        return 'cooking'
    
    # Default to other/don't know when no type signal found
    return "other/don't know"


def determine_controversial(title, text_raw):
    """Y when content involves political attacks, immigration, EEOC, administration controversy."""
    text_lower = html.unescape(text_raw).lower()
    title_lower = title.lower()
    
    controversial_keywords = [
        'eeoc', 'immigration', ' deportation', 'trump administration',
        'attacks on the press', 'free speech', 'first amendment',
        'government censorship', 'politically motivated', 'alleging employment bias',
        'anti-semitism', 'desegregation', 'civil rights', 'hate crime',
        'political pressure', 'adminisration attacks', 'threatened to revoke',
        'administration targeting'
    ]
    
    # Explicit political/administrative attack language
    if any(w in text_lower for w in ['eeoc lawsuit', 'politically motivated allegations',
                                        'trump administration', 'attacks on the free press',
                                        'escalating attacks on the press']):
        return 'Y'
    if 'categorically rejects' in text_lower:
        return 'Y'
        
    # Immigration/deportation related (political but not necessarily "controversial" NYT coverage)
    if any(w in title_lower for w in ['immigration', 'deportation']):
        return 'Y'
    
    # EEOC or government legal action
    if 'eeoc' in text_lower:
        return 'Y'
        
    # Administration attacks on press
    if any(w in title_lower for w in ['attacks on', 'free press']):
        return 'Y'
    
    return 'N'


def determine_relevant(url, title, text_raw):
    """Y when content relates to NY-based operations or major NYT/national impact."""
    text_lower = html.unescape(text_raw).lower()
    title_lower = title.lower()
    
    # Direct relevant signals
    if any(w in title_lower for w in ['new york', 'ny', 'times square', 
                                          'manhattan'] +
               [w for w in ['trump towers', 'white house']]):
        return 'Y'
    
    # NY-specific operations
    ny_signals = ['new york climate week', 'jazz at lincoln center', 'citi concert series',
                   'united nations general assembly', 'onyx', 'the daily new york',
                   'new york magazine']
    if any(w in text_lower for w in ny_signals):
        return 'Y'
    
    # National/important content = relevant
    important_signals = ['pulitzer prize', 'emmy award', 'national book award', 
                         'dealbook summit', 'the new york times games',
                         'wordle', 'connections puzzle', 'spelling bee',
                         'the daily podcast', 'wirecutter', 'cooking',
                         'nyt cooking', 'athletic world cup', 'serial productions']
    if any(w in text_lower for w in important_signals) or any(w in title_lower for w in important_signals):
        return 'Y'
    
    # Staff announcements with national scope are relevant
    if any(w in title_lower for w in ['pew research center', 'national book award:', 
                                        '$100,000']:
            return 'Y'
    
    # Company product launches for NYT itself = relevant
    if any(w in url for w in ['nytco.com/press/products/', '/app/']):
        return 'Y'
        
    return 'N'


# --- MAIN EXECUTION ---
print('Loading source data...')
with open(SOURCE_PATH, encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    rows = [row for row in reader]

print(f'Classifying {len(rows)} rows...')
results = []
for i, row in enumerate(rows):
    result = classify(row)
    results.append(result)
    if (i + 1) % 500 == 0:
        print(f'  Processed {i+1}/{len(rows)} ({(i+1)/len(rows)*100:.0f}%)')

# Write output
print(f'\nWriting output to {OUTPUT_PATH}...')
with open(OUTPUT_PATH, 'w', newline='', encoding='utf-8-sig') as f:
    fieldnames = ['urls', 'fullText', 'storyTitle', 'datePublished', 'dateModified',
                  'Category', 'Type', 'Controversial (Y/N)', 'Relevant (Y/N)']
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(results)

# Summary stats
cats = Counter(r['Category'] for r in results)
types = Counter(r['Type'] for r in results)
controversial = Counter(r['Controversial (Y/N)'] for r in results)
relevant = Counter(r['Relevant (Y/N)'] for r in results)

print(f'\n=== CLASSIFICATION SUMMARY ({len(results)} rows) ===')
print('\nCategories:')
for c, n in sorted(cats.items(), key=lambda x: -x[1]):
    print(f'  {c:25s}: {n:5d} ({n/len(results)*100:5.1f}%)')

print('\nTypes:')
for t, n in sorted(types.items(), key=lambda x: -x[1]):
    print(f'  {t:25s}: {n:5d} ({n/len(results)*100:5.1f}%)')

print('\nControversial:')
for c, n in sorted(controversial.items(), key=lambda x: -x[1]):
    print(f'  {c:25s}: {n:5d}')

print('\nRelevant:')
for r, n in sorted(relevant.items(), key=lambda x: -x[1]):
    print(f'  {r:25s}: {n:5d}')

# Cross-tabulation for validation
print('\n=== Category x Type cross-tab (top 20) ===')
ct = Counter()
for r in results:
    ct[(r['Category'], r['Type'])] += 1
for (cat, typ), n in sorted(ct.items(), key=lambda x: -x[1]):
    print(f'  {cat:25s} x {typ:25s}: {n}')

print('\nDone!')
