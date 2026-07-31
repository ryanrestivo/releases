#!/usr/bin/env python3
"""
Classifiers for NYT Press Releases
===================================

This module contains all classifiers used to categorize press releases from the New York Times.
Each classifier has clear rules, edge cases, and test scenarios documented in comments.

Categories (hierarchical):
1. award - Journalism awards, honors, recognitions given TO the NYT
2. staff announcement - Hires, promotions, departures within NYT
3. company update - Product launches, business decisions, strategy posts
4. fact check - Fact-checking articles published by NYT
5. feature - Long-form editorial/investigative pieces
6. statement - Official statements/responses from NYT

New flags (for future-proofing):
- is_product_launch: Y/N for new tools/apps/tech releases
- is_event_announcement: Y/N for summits/festivals/events
- is_newsletter_expansion: Y/N for newsletter launches or expansions

Classifiers are evaluated in priority order (most specific first):
1. Statement → official NYT response 
2. Fact check → fact-checking content
3. Award → journalism awards received by NYT
4. Feature → long-form editorial work
5. Staff announcement → personnel changes
6. Company update → catch-all for remaining business activities

For future releases: run all classifiers and assign based on text similarity + rules defined below.
"""

import csv
from collections import Counter, defaultdict
from typing import Dict, List, Optional, Tuple


# ============================================================================
# CLASSIFIER DEFINITIONS
# ============================================================================

classifiers = {
    'statement': {
        'description': 'Official statement or public response issued by The New York Times',
        'primary_signals': [
            'responds to',
            'supports campaign', 
            'official statement',
            'responding to lawsuit',
            'our position'
        ],
        'exclusion_signals': [
            'award', 'won ', 'emmy', 'pulitzer',  # Not an announcement of receipt
        ],
        'test_scenario': '''
Example input: "The New York Times Responds to Lawsuit Filed by President Donald Trump"
Expected category: statement
Reasoning: Contains 'responds to' + mentions lawsuit → official NYT response
''',
        'priority': 10,
    },
    
    'fact_check': {
        'description': 'Articles specifically fact-checking claims (usually political)',
        'primary_signals': [
            'false claims',
            'misinformation ',
            'fabricated',
            'fact check',
            'fact-checking'
        ],
        'exclusion_signals': [
            'emmy', 'honored with', 'won ',  # Awards, not fact checks
            'wins ', 'received the'
        ],
        'test_scenario': '''
Example input: "Fact-Checking Claims About Our Coverage of ActBlue"  
Expected category: fact check
Reasoning: Contains 'fact-checking claims' → direct content about checking misinformation
''',
        'priority': 4,
    },
    
    'award': {
        'description': 'Honors, awards, or recognitions received BY The New York Times (not for staff)',
        'primary_signals': [
            'won ', 'emmy', 'pulitzer', 'effie', 'national magazine award',
            'honored with', 'received the ', 'wins ',
            'award'  # When combined with other award signals
        ],
        'exclusion_signals': [
            'joins the', 'join the desk,', 'named assistant', 'returning to'  # Staff moves
        ],
        'test_scenario': '''
Example input: "The New York Times Won Three Emmys for its Coverage of..."
Expected category: award
Reasoning: Contains 'won' + 'emmy' → NYT received an award

Example input: "Jody Quon Is T Magazine's Next Editor in Chief"
Expected category: staff announcement  (NOT award)
Reasoning: Although it has title-like structure, it describes a personnel change, not an honor received.
''',
        'priority': 3,
    },
    
    'feature': {
        'description': 'Long-form editorial/investigative pieces (not business announcements)', 
        'primary_signals': [
            'investigating',
            'deep dive into',
            'exploration of the',
            "what it's like"  # Personal experience pieces
        ],
        'exclusion_signals': [
            'joins the', 'is named ', 'new role for', 'returning to'  # Staff/corporate
        ],
        'test_scenario': '''
Example input: "Investigating the Hidden World of..."
Expected category: feature
Reasoning: 'investigating' suggests long-form journalism, not business news

Example input: "'New York Times Magazine Publishes Special Report on Climate Change...'"
Expected category: feature  
Reasoning: 'magazine' + 'special report' → editorial/investigative content
''',
        'priority': 5,
    },
    
    'staff_announcement': {
        'description': 'Personnel changes: new hires, promotions, departures within NYT organization',
        'primary_signals': [
            'joins ', 'join the desk', 
            'named assistant/associate/editor-in-chief/publisher/etc.',  # Specific title formats
            'is promoted to',
            'returning to ',
            'promotions in',
            'hired as'
        ],  
        'exclusion_signals': [
            'won ', 'emmy', 'pulitzer', 'award',  # Awards received by staff, not staff news
            'joins the board'  # External appointment
        ],
        'test_scenario': '''
Example input: "A.G. Sulzberger Appointed Publisher of The New York Times"
Expected category: staff_announcement
Reasoning: Contains 'appointed' + specific role → new hire/promotion

Example input: "Promotions in Opinion: Lauren Leibowitz Joins Times Opinion..."
Expected category: staff_announcement  
Reasoning: Explicitly mentions promotions, uses 'joins' format
''',
        'priority': 6,
    },
    
    'company_update': {
        'description': 'Business activities, product launches, strategy updates from NYT organization/corporate',
        'primary_signals': [
            'app launch', 'tool launch', 'we have launched', 'announcing a tool',  # Tech releases
            'productivity tool', 'available to public', 
            'new role', 'strategic initiative',
            'revenue announcement', 'company report'
        ],
        'exclusion_signals': [
            'joins the desk', 'promotion for', 'hired as',  # Staff moves
            'award', 'won ',  # Awards 
            'investigating', 'deep dive into'  # Editorial content
        ],  
        'test_scenario': '''
Example input: "Introducing our first tool to help track news over time..."
Expected category: company_update
Reasoning: 'tool' + 'launch/release' → business/tech activity

Example input: "Our quarterly plan for revenue growth and expansion plans"  
Expected category: company_update
Reasoning: Business strategy report, not editorial content
''',
        'priority': 7,
    },
}


# ============================================================================
# NEW FLAG CLASSIFIERS (for future-proofing)
# ============================================================================

new_flags = {
    'product_launch': {
        'description': 'New tools, apps, subscriptions or tech releases launched by NYT',
        'signals': [
            'new productivity tool', 
            'tool available to the public',
            'we have launched', 
            'brand new app', 
            'just launched a tool'
        ],
        'test_scenario': '''
Example: "Chronicle: The Tool That Helps Track New York Times Language..."
Expected flag: is_product_launch = Y
Reasoning: Contains 'tool' + public release → product launch category
'''},

    'event_announcement': {
        'description': 'Summits, festivals, conferences, or livestream events hosted by NYT',  
        'signals': [
            'dealbook summit', 
            'milan digital fashion week', 
            'livestream collaboration with', 
            'annual dealbook',
            'local investigations fellows',  # Fellowship event
            'festival of literature 20' 
        ],
        'test_scenario': '''
Example: "The New York Times Unveils Mainstage Interviews at Annual DealBook Summit..."
Expected flag: is_event_announcement = Y  
Reasoning: Conference/summit format → event announcement category.
'''},

    'newsletter_expansion': {
        'description': 'New newsletter launches, expansions to existing newsletters',  
        'signals': [
            'launch local newsletter', 
            'announcing our next edition of',
            'launching a local newsletter program'
        ],
        'test_scenario': '''
Example: "The New York Times to Launch Local Newsletter in the Twin Cities"
Expected flag: is_newsletter_expansion = Y  
Reasoning: Explicitly mentions launching a new regional/niche newsletter.
'''},
}


# ============================================================================
# CLASSIFICATION ENGINE
# ============================================================================

def classify_release(row_data: Dict[str, str]) -> Dict[str, any]:
    """
    Classify a single press release using both the base category system and new flags.
    
    Args:
        row_data: Dictionary containing 'storyTitle', 'fullText' keys
        
    Returns:
        Dictionary with 'category' (base class) and new flag values
        
    Example usage:
        result = classify_release({
            'storyTitle': 'A.G. Sulzberger Appointed Publisher',
            'fullText': 'The New York Times Company today announced...'
        })
        # Returns: {'category': 'staff_announcement', 
                   'is_product_launch': 'N', 
                   'is_event_announcement': 'N',
                   'is_newsletter_expansion': 'N'}
    """
    
    story_title = row_data.get('storyTitle', '').lower()
    full_text = (row_data.get('fullText') or '').lower()  
    combined_text = f'{full_text} {story_title}'
    
    # Initialize with default category (most general catch-all)
    classified_category = 'company_update'  # Default if nothing else matches
    highest_priority_rule = ''
    
    # Evaluate classifiers in priority order
    for class_name, classifier in sorted(classifiers.items(), key=lambda x: x[1]['priority']):
        primary_hit = any(signal in combined_text for signal in classifier['primary_signals'])  
        exclusion_hit = any(signal in combined_text for signal in classifier['exclusion_signals'])
        
        if primary_hit and not exclusion_hit:
            classified_category = class_name  # More specific matches override less specific ones
            highest_priority_rule = f"matched {class_name} with primary_hits" 
            break  # Found the most specific match
            
    elif excluded_text in combined_text:
        classified_category = 'statement' 
        
    # Check for new flags
    is_product_launch, is_event_announcement, is_newsletter_expansion = (
        _check_new_flags(combined_text)
    )
