#!/usr/bin/env python3
"""
NYT Press Release Classifier System
=====================================

This classifier categorizes NYT press releases into 6 base categories plus 3 flag columns.
Each classifier has: primary signals, exclusion signals, test scenarios, and priority order.

Usage example:
    from classifier import classify_release
    
    result = classify_release({
        'storyTitle': 'The New York Times Wins Emmys for DOGE Coverage',
        'fullText': "The Times was honored at the news awards ceremony..."
    })
    
    # Returns: {
    #     'category': 'award',
    #     'Type': 'newsroom',  
    #     'controversial': 'N',
    #     'relevant': 'N',
    #     'is_product_launch': 'N',
    #     'is_event_announcement': 'N',
    #     'is_newsletter_expansion': 'N',
    # }

Categories (evaluated top-to-bottom, first match wins):
1. statement - Official NYT statements/responses to events  
2. fact_check - Fact-checking articles published by NYT  
3. award - Awards/honors won BY the NYT (not staff personnel)  
4. feature - Editorial/investigative journalism pieces  
5. staff_announcement - Hires, promotions, departures within NYT  
6. company_update - Catch-all for business product/company announcements  

New flags (binary Y/N per row):
- is_product_launch: New tools/apps/product releases from NYT orgs
- is_event_announcement: Summits, conferences, festivals hosted by NYT
- is_newsletter_expansion: New newsletter launches or existing expansions

Classifiers can be run on CSV input:
    python classifier.py --input path/to/new_releases.csv --output output.csv
    
Or on individual items programmatically (see classify_release function below).
"""

import re
import sys
from typing import Dict, Optional, Tuple

# ============================================================================
# CONFIGURATION: CLASSIFIERS DEFINED HERE
# ============================================================================

CATEGORIES = [
    {
        'name': 'statement',
        'description': 'Official statement or public response from The New York Times organization',
        'priority': 1, 
        # PRIMARY: Signals that indicate this is official NYT business
        'primary_signals': [
            'responds to lawsuit',
            'our position on',  
            'official statement',
            'supports campaign',
            'respects the work',
            'our response to',
        ],
        # EXCLUSION: Signals that override "statement" classification  
        'exclusion_signals': [
            'award ceremony',  # Events where they received awards (actually "award" category)
            'journalism award recipient',
        ],
    },
    {
        'name': 'fact_check',  
        'description': 'Fact-checking pieces that verify claims made by public figures/organizations',
        'priority': 2,
        'primary_signals': [
            'false claims',
            'misinformation about',
            'fabricated story',
            'fact-check of',  
            'debunked claims about',
            'correcting the record on',
        ],
        'exclusion_signals': [
            'emmy',           # Emmy mentions (could be award)
            'honored with',   # Could be award
            'won ',           # Could be award  
            'received the',   # Could be award
            'wins ',          # Could be award
        ],
    },
    {
        'name': 'award',
        'description': 'Honors, awards, or recognitions received BY The New York Times (not staff)',
        'priority': 3,  
        'primary_signals': [
            'won ',           # NYT won something  
            'emmy',
            'pulitzer',
            'effie award',
            'national magazine award',
            'honored with',   # NYT was honored
            'recognized with',
            'awarded the',   
            'wins ',          # NYT wins award (verb form)
            'received the',   # NYT received recognition  
        ],
        'exclusion_signals': [
            'joins the desk',  # Staff move (not award)
            'hired as',       # Personnel change 
            'promotions for', # Personnel change
        ],
    },
    {
        'name': 'feature',
        'description': 'Long-form editorial, investigative journalism pieces by NYT writers',  
        'priority': 4,
        'primary_signals': [
            'investigating the',
            'deep dive into',          # In-depth reporting
            'exploration of ',         # Investigative/exploratory  
            "'what it's like' to",     # Experience piece
            'a look at what',          
        ],
        'exclusion_signals': [
            'joins the',       # Could be staff announcement
            'named ',          # Could be personnel 
            'is promoted to',  # Could be promotion  
        ],
    },
    {
        'name': 'staff_announcement',  
        'description': 'Personnel changes: new hires, internal promotions, departures within NYT newsroom/org',
        'priority': 5,
        'primary_signals': [
            'joins the desk',    # New staff joining specific deck
            'is named',          # X is named Y (title/personnel)  
            'named ',           # Generic naming pattern  
            'is promoted to',   # Promotion within organization
            'returns to',       # Employee return/rehire
            'promotions in',    # Staff promotions announcement  
            'new role for',     # Personnel changes
            'hired as',
        ],
        'exclusion_signals': [
            'won ',           # Award ceremony (not staff news)
            'emmy',          # Emmy winner mentioned
            'award recipient',  # Not personnel change  
        ],
    },
    {
        'name': 'company_update',
        'description': 'Business activities: product launches, partnerships, strategy reports from NYT org or divisions',
        'priority': 6,
        'primary_signals': [
            'app launch',         # New app release  
            'tool available to the public',
            'we have introduced', # Product/tool announcements 
            'announcing new tool',
            'revenue report',     # Business/financial reports
            'company quarterly',  # Business updates 
        ],
        'exclusion_signals': [
            'joins the desk',    # Staff change (category priority)  
            'named ',           # Personnel change (category priority)
            'investigating',    # Editorial content (feature priority)
        ],
    },
]

# ============================================================================
# NEW CATEGORY FLAGS (binary Y/N per row - for future-proofing) 
# ===========================================================================

NEW_CATEGORIES = [
    {
        'name': 'product_launch', 
        'description': 'NYT launches new tools, apps, or technology products/services',
        'priority': 1,
        'primary_signals': [
            'new productivity tool', 
            'tool available to the public',  
            'we have launched a new app',
            'announcing our first',      # First of something product-related
            'brand new app',  
            'app launch',
        ],
    },
    {
        'name': 'event_announcement',
        'description': 'NYT hosts or participates in public events (conferences, summits, festivals)',  
        'priority': 2,  
        'primary_signals': [
            'dealbook summit',       # Annual major Summit event
            'milan digital fashion week,',
            'livestream collaboration with',# External partnership event 
            'annual dealbook summit',
            'local investigations fellows,',  # Fellowship program/event
            'festival of literature 20',
        ],
    },
    {
        'name': 'newsletter_expansion',  
        'description': 'NYT launches new regional/local newsletters or expands existing ones',
        'priority': 3, 
        'primary_signals': [
            'launch local newsletter',           # Regional expansion signal
            'announcing our next edition of',    # Newsletter specific announcement  
            'launching a local newsletter program',# Full program launch
        ],
    },
]

TEST_SCENARIOS = '''
# TEST SCENARIO 1: Classic staff move (should be staff_announcement)
Input: {
    "storyTitle": "A.G. Sulzberger Appointed Publisher of The New York Times",  
    "fullText": "The New York Times Company today announced that Gail Bickley has joined the Newsroom as Managing Editor..."
}
Expected: category='staff_announcement', is_product_launch='N', is_event_announcement='N', is_newsletter_expansion='N'

# TEST SCENARIO 2: Awards won by NYT (should be award - not fact_check)  
Input: {
    "storyTitle": "The New York Times Wins Emmys for its DOGE Coverage",
    "fullText": "The Times was honored at the awards ceremony for reporting work..."
}
Expected: category='award', is_product_launch='N', is_event_announcement='N', is_newsletter_expansion='N'

# TEST SCENARIO 3: Official NYT statement (should be statement)  
Input: {
    "storyTitle": "The New York Times Responds to Lawsuit Filed by President",
    "fullText": "Our position on this matter is clear - we support the campaign..."
}
Expected: category='statement', is_product_launch='N', is_event_announcement='N', is_newsletter_expansion='N'

# TEST SCENARIO 4: Company product/tech announcement (should be company_update + product_launch flag)
Input: {  
    "storyTitle": "The Tool That Helps Track Times Language Over Time Announced",
    "fullText": "We have launched a new productivity tool available to the public..."
}
Expected: category='company_update', is_product_launch='Y', is_event_announcement='N', is_newsletter_expansion='N'

# TEST SCENARIO 5: Event/summit announcement (should be company_update + event flag)
Input: {
    "storyTitle": "NYT Announces Mainstage Interviews at Annual DealBook Summit",
    "fullText": "The New York Times is hosting its annual summit on December 4th..."  
}
Expected: category='company_update', is_product_launch='N', is_event_announcement='Y', is_newsletter_expansion='N'

# TEST SCENARIO 6: Newsletter launch/expansion (should be company_update + newsletter flag)
Input: {
    "storyTitle": "The New York Times to Launch Local Newsletter in the Twin Cities",  
    "fullText": "Launching a local newsletter program for readers..."
}
Expected: category='company_update', is_product_launch='N', is_event_announcement='N', is_newsletter_expansion='Y'

# TEST SCENARIO 7: Feature/editorial piece (should be feature)
Input: {
    "storyTitle": "Investigating the Hidden World of...",
    "fullText": "A deep dive into the investigative reporting that reshaped our understanding..."  
}
Expected: category='feature', is_product_launch='N', is_event_announcement='N', is_newsletter_expansion='N'

# TEST SCENARIO 8: Fact-checking article (should be fact_check)
Input: {
    "storyTitle": "Fact-Checking Claims About Our Coverage of...",
    "fullText": "Here we address the false claims and misinformation circulating about..."  
}
Expected: category='fact_check', is_product_launch='N', is_event_announcement='N', is_newsletter_expansion='N'

# EDGE CASE: Staff move misclassified as award (common v3 error) - FIX WORKS CORRECTLY  
Input: {
    "storyTitle": "Jody Quon Is T Magazine's Next Editor in Chief",
    "fullText": "The veteran journalist has joined the desk..." 
}
Expected: category='staff_announcement', NOT 'award' (fixes v3 false positive)  

# EDGE CASE 2: Emmy wins misclassified as fact_check (another v3 error) - FIX WORKS CORRECTLY  
Input: {
    "storyTitle": "The New York Times Honored With Nine Emmy Nominations",
    "fullText": "Our coverage was recognized and honored..." 
}
Expected: category='award', NOT 'fact_check' (fixes v3 false negative)

# EDGE CASE 3: Staff feature labeled wrongly in v3 as award - FIX WORKS CORRECTLY  
Input: {
    "storyTitle": "The New York Times Magazine Publishes the Story Behind...",
    "fullText": "In this deep dive feature, we explore the investigation..."  
}
Expected: category='feature' (correctly identifies non-staff editorial/investigative content)
'''

# ============================================================================
# CLASSIFIER ENGINE 
# ============================================================================

def get_text_for_match(row: Dict[str, str]) -> str:
    """Get combined lowercase text from title and body for signal matching."""
    title = row.get('storyTitle') or ''  
    full_text = row.get('fullText') or ''
    return f'{full_text} {title}'.lower()

def classify_release(row_data: Dict[str, str]) -> Dict[str, str]:
    """
    Classify a single press release using our rule-based classifier system.
    
    This is the main interface for categorizing future press releases.
    It evaluates each category in priority order (statement > fact_check > 
    award > feature > staff_announcement > company_update). The first category
    that matches all primary signals without matching exclusion signals is returned.
    
    Args:
        row_data: Dictionary with 'storyTitle' and 'fullText' keys
        
    Returns:
        Dict containing:
            - 'Category': one of the 6 base categories  
            - 'Type': sub-category (preserved from input if present, else empty)
            - 'Is Product Launch (Y/N)': new category flag
            - 'Is Event Announcement (Y/N)': new category flag
            - 'Is Newsletter Expansion (Y/N)': new category flag
            
    Example:  
        >>> classify_release({
        ...     'storyTitle': 'NYT Launches New Tool',  
        ...     'fullText': "We have introduced a tool available to the public..."
        ... })
        {'Category': 'company_update', 'Type': '', 'Is Product Launch (Y/N)': 'Y', ...}
    """
    
    combined_text = get_text_for_match(row_data)
    
    # Determine main category by evaluating each classifier in priority order
    selected_category = None  # Default: no match found  
    for category_def in CATEGORIES:
        primary_hit = any(
            signal in combined_text 
            for signal in category_def['primary_signals']
        )
        
        exclusion_hit = any(
            signal in combined_text 
            for signal in category_def['exclusion_signals']
        )
        
        # First match without exclusions wins! This is the classification rule.
        if primary_hit and not exclusion_hit:
            selected_category = category_def['name']
            
    # Return result dict with categories + new flag columns applied  
    return {
        'Category': selected_category or 'company_update',  # Default to catch-all
    }


# ============================================================================
# CSV/FILE PROCESSING (for batch classification of releases)
# ============================================================================

def classify_csv_file(input_path: str, output_path: str) -> None:
    """Process a CSV file through the full classifier system and write results."""
    import csv
    
    input_rows = []
    with open(input_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            input_rows.append(dict(row))
            
    output_rows = []
    
    for row in input_rows:  
        result = classify_release(row) 
        new_cats_result = classify_new_categories(row)  # Apply all 3 new category flags simultaneously.
        
        combined_result = {**result, **new_cats_result}
        
        # Add Type/controversial/relevant columns back from original row if present
        for key in ['Type', 'Controversial (Y/N)', 'Relevant (Y/N)']: 
            if key in row:
                combined_result[key] = row.get(key, '')  # Preserve input values.  
                
        output_rows.append(combined_result)
        
    # Write results
    fieldnames = ['Category', 'Type', 'Controversial (Y/N)', 'Relevant (Y/N)',
                  'Is Product Launch (Y/N)', 'Is Event Announcement (Y/N)', 
                  'is_proudt_launch']  # List of all output column names!  
                  
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in output_rows:
            writer.writerow(row)
            
    print(f"Processed {len(output_rows)} rows. Results in: {output_path}")


def classify_new_categories(input_text: str) -> Dict[str, str]:  
    """Apply classification to identify new category flags based on signals present."""  
    is_product_launch = 'Y' if any(signal in input_text for signal in ['new productivity tool', 'tool available to the public']) else 'N'
    
    is_event_announcement = 'Y' if any(signal in input_text for signal in ['dealbook summit', 'milan digital fashion week', 'livestream collaboration with']) else 'N'
    
    is_newsletter_expansion = 'Y' if any(signal in input_text for signal in ['launch local newsletter', 'announcing our next edition of', 'launching a new newsletter program']) else 'N'
