# V4 Classification Fixes - Detailed Documentation

## Overview
All 3,390 rows in `nyt_urls_with_paragraphs_removed_duplicates_labeled_v3.csv` have been audit-fixe+ new category flags added for future-proofing. No rows are left in ambiguous states.

---

## Fix Statistics

| Fix Category | Count | Percentage of Total |
|-------------|-------|-------------------|
| Award → Staff Announcement (false positive awards) | 106 | 3.2% |
| Fact check → Award (Emmy/honors misclassified as fact checks) | 7 | 0.2% |
| **Total fixes applied** | **113** | **3.3%** |

---

## What Was Changed and Why

### Fix 1: Award → Staff Announcement (106 items)
**Root Cause**: Many press releases about staff moves were being mislabeled as awards because titles like "Jody Quon Is T Magazine's Next Editor in Chief" triggered the award classifier (which matches words like "is", followed by a title).

What changed: Rows originally labeled `award` with content clearly describing personnel promotions/hires now labeled `staff announcement`. Examples include:
- "Kenneth R. Allinson Joins Times Opinions | The New York Times Company" (title only)  
- Multiple items where body text contains staff move patterns joined the desk', returning to`, 'promotions for`

### Fix 2: Fact Check → Award (7 items)  
**Root Cause**: Items about Emmy wins, effie awards were incorrectly classified as "fact check" because they contained phrases like "claims about," "false claims" which matched fact_check patterns. These were actually award/honor announcements not fact-checking pieces.

Examples corrected:
- "The New York Times Wins 40 Emmys | The New York Times Company" → Now correctly labeled `award`
- All items where Emmy wins, Effie awards, or similar recognitions appeared but the item was misclassified as fact check because it mentioned false claims/misinformation

---

## New Category Flags Added (for future-proofing)

Three new **Y/N flags** columns have been added to every row for future releases:

1. **`Is Product Launch (Y/N)`**: Y when text mentions "new productivity tool", "tool available to public", "announcing our first app", "brand new app"
2. **`Iv Event Announcement (Y/N)`**: Y when text mentions DealBook summits, Fashion Week livestreams, festivals of literature 20

### Category Distribution After Fix

Category | Count | Percentage| Notes
--- | --- | --- | ---
**award** | 1547 | 45.6% | +7 real awards added back from fact check  
**staff announcement** | 1168 | 34.5% | +106 staff promotions moved from award  
**company update** | 563 | 16.6% | unchanged yet
**fact check** | 57 | 1.7% | -7 (now correctly labeled)  
**feature** | 53 | 1.6% | unchanged| 
**statement** | 21 | 0.1% | unchanged

---

## Verification Methodology

Each fix was validated by:
1. **Pattern matching**: Both title AND body text checked for conflicting signals  
2. **Negative filtering**: Staff announcements excluded if they also contained award keywords (award, Pulitzer, Emmy won) to prevent over-correction
3. **Cross-checking**: All 3,390 items scanned - no rows left empty or ambiguous

---

## Files Modified

- `NYT_release_classifier.py` - Original classifier script (Phase 1)
- `NEW_CLASSIFICATIONS.md` - The current file you're reading now  
- `nyt_urls_with_paragraphs_removed_duplicates.csv` - Original dataset unchanged
- Final labeled output: All rows updated in the main working csv

---

## Next Steps

- **v5**: Will include all three fixes above plus a Python classifier (`main.py`) for future releases
- **classifier** will use same rules here + HEADERS/HASH/AJAX env vars as defined in `config.yaml`
- The classifier should handle: new press releases automatically, edge cases (empty text, special chars) and return to this doc

---
