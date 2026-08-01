#!/usr/bin/env python3
"""
Labeled: 3,490 NYT press releases with Category, Type, Controversial (Y/N), Relevant (Y/N).

Priority order: statement > fact_check > award > feature > staff_announcement > company_update
    
Reference: 81 labeled examples + full-scan pattern analysis.
"""

import csv
import html
from collections import Counter


def classify_category(title_raw, text_raw):
    title = (title_raw or '').strip()
    raw_text = html.unescape(text_raw or '')
    t = title.lower()
    tx = raw_text.lower()
    c = f"{tx} {t}"
    
    # 1. STATEMENT  
    stmt_kw = 'eeoc', 'lawsuit', 'categorically rejects', "our position on immigration", \
        'denies allegations'
    if any(kw in c for kw in stmt_kw):
        return 'statement'
    if 'response to eeoc' in t and ('rejects' in c or 'denial' in c):
        return 'statement'


    # === 2. FACT CHECK (priority 2) ===
    if 'fact-checking false claims' in t:
        return 'fact_check'
    
    if 'false claims about our' in c:
        return 'fact_check'
    
    # === 3. AWARD (priority 3) - with EXCLUSION for Wirecutter/crossword games ===
    
    # EXCLUSION 1: wirecutter product awards are NOT media awards
    if 'wirecutter best picks' in c or 'best new picks award' in c:
        return 'company_update'
    
    # EXCLUSION 2: crossword/puzzle references
    if any(kw in c for kw in ['crossword ', 'crosswords:', 'spelling bee scores',
                               'connections leaderboard', 'leaderboard']):
        return 'company_update'
    
    # Strong award signals ALWAYS (unambiguous)
    strong_award = [
        'pulitzer prize',
        'emmy nomination', 'emmy win', 'honored with nine emmy', 'news and documentary emmy',
        'national book award winner', 'pulitzer, the national magazine award',
        'polk award', 'overseas press club', 'opc award',
        'osborn elliot prize', 'james c. goodale first amendment award',
        'gwen ifill press freedom award',
    ]
    if any(s in c for s in strong_award):
        return 'award'
    
    # "Wins" or "won" title patterns (Times wins awards)
    if re.search(r'\bwins\b', t.lower()):
        has_media_awd = any(kw in t.lower() for kw in ['emmy', 'award', 'prize'])
        has_award_in_text = any(kw in tx for kw in ['awarded by the', 'was honored with ', 
                                                      'has been awarded', 'recognized at the',
                                                         "receiving the", "honored at",
        ])
        if has_media_awd or has_award_in_text:
            return 'award'}
