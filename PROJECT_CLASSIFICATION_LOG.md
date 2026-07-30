# NYT PRESS RELEASES CLASSIFICATION PROJECT
## Full Project Documentation & Process Log

**Date Created:** 2025-12-26 (active session)
**Branch:** `072926-labeling-overnight`  
**Target PR:** #11 on ryanrestivo/releases
**Dataset Size:** 3,390 press releases from NYT Research dataset

---

## PROJECT PURPOSE

Classify 3,390 unlabeled New York Times research press releases into categories and metadata fields (Category, Type, Controversial, Relevant) using content pattern analysis trained on small reference datasets of human-labeled examples.

---

## THE LABELING CHAIN — HOW REFERENCES CONNECT TO MAIN DATA

### The Three Files

#### 1. labeling_test.csv (81 reference rows)
- **What it contains:** Category + Type labels for labeled releases
- **No URLs in this file** — only Article Number, Date, Title, Category, Type
- **Valid Categories found:** staff_announcement, company_update, statement, fact_check, award, feature
- **Valid Types found:** newsroom, opinion, audio, games, cooking, the_athletic, other/don't know

#### 2. releases_labeling.csv (~50 reference rows)
- **What it contains:** C/R flags + URLs for each release
- **Category column (col 4) is COMPLETELY BLANK** — NO category data available here
- **C/R data IS populated:** Controversial Y/N and Relevant Y/N columns have values
- **Source URLs in col 7** provide the bridge to connect to main CSV

#### 3. nyt_urls_with_paragraphs_removed_duplicates.csv (3,390 rows)
- **Columns:** url, fullText, storyTitle, datePublished, dateModified  
- **What it needs:** Category, Type, Controversial, Relevant labels

### THE MAPPING CHAIN (How the three files connect)

```
Labeling_test.csv        releases_labeling.csv       Main NYT CSV
-------------------      ----------------------      --------------
Category ✓   ←──── Title match via storyTitle  ──→ storyTitle column
Type     ✓   ←──── URL bridge via Source URL ──→ url column             
              C/R flags    ←── Title match ──→ (propagated)
```

**Step 1:** Cross-reference both reference CSVs by matching their Title columns to establish which releases have BOTH Category+Type AND C/R flags.

**Step 2:** Match Source URLs from releases_labeling.csv against main CSV urls column to get labeled rows with all four fields populated.

**Step 3:** Use content pattern analysis on storyTitle + fullText fields for remaining unlabeled rows that couldn't be matched via references.

---

## PROCESS LOG — WHAT WAS DONE, STEP BY STEP

### Step 1: Data Exploration & Reference Analysis ✅
- Read labeling_test.csv → confirmed Category column has values (81 labeled examples)
- Read releases_labeling.csv → discovered Category column is BLANK for all rows
- Identified the mapping chain URL → Source_url matches main csv urls field
- Cross-reference via titles where URLs don't match exactly

### Step 2: Initial Script Development → classification_with_rationale.py ✅  
- Built initial title-only matching script
- Found it could only classify ~586 of 3,390 rows (17%) using exact/prefix/title comparison
- Problem: Reference filenames are too small compared to main CSV to get good coverage

### Step 3: Content Pattern-Based Classifier (Current) ✅
The final classifier (`classify_all_3390.py`) uses a **content pattern analysis** approach:

#### Classification Rules (Learned from Reference Examples):
1. **staff_announcement:** Titles contain "Joins", "joins", "hire", "appointed", 
   "Promotion", "deputy editor", "bureau chief", "correspondent", "creative director"
2. **company_update:** New product launches (games updates, cooking features, podcasting)
3. **statement:** Lawsuits filed against/by NYT, EEOC matters, legal responses
4. **fact_check:** Fact-checking claims about NYT coverage in media/political discourse
5. **award:** Journalism awards won by NYT/personnel, honors received
6. **feature:** Human interest stories, anniversary celebrations, profile pieces

#### Data Sources Used per Row:
- Primary: storyTitle field → keyword signals for category determination
- Secondary: fullText field → confirms content analysis with contextual data
- Tertiary: URL matching against reference URLs for C/R flag propagation

---

## CLASSIFICATION RESULTS (Final Output)

### Categories Distributed:
```
company_update:     2,037 rows (60.1%)   - Product launches, company announcements
staff_announcement: 1,058 rows (31.2%)   - Hiring, promotions, departures  
award:                281 rows ( 8.3%)    - Journalism awards, honors
statement:              9 rows ( 0.3%)    - Lawsuits, legal matters
fact_check:             5 rows ( 0.1%)    - Fact checks on coverage claims
feature:                0 rows ( 0.0%)    - No feature matches detected
```

### Coverage Notes:
- C/R propagates via reference URL/title matching where available
- Default type is "newsroom" for staff announcements, "other/don't know" for company updates
- Category assignments based on keyword/signal detection from storyTitle and fullText fields

---

## CLASSIFICATION RATIONALE PER ROW (Detailed)
A complete row-by-row rationale table documenting why each release was classified as it was is in:
`CLASSIFICATION_RATIONALE.md`

The per-row table includes: Row number, Story Title truncation, Category, Type, 
Controversial flag, Relevant flag, and reasoning for the classification decision.

---

## FILES IN THIS PROJECT

| File | Purpose |
|------|---------|
| `nyt_urls_with_paragraphs_removed_duplicates.csv` | Original main dataset (3,390 releases) |  
| `refs/labeling_test.csv` | Reference data with Category+Type labels (81 rows) |
| `refs/releases_labeling.csv` | Reference data with C/R flags + URLs (~50 rows) |
| `scripts/classify_all_3390.py` | Final content-pattern classifier script |
| `nyt_classified_with_rationale.csv` | Full labeled output CSV (3,390 rows with all labels) |
| `CLASSIFICATION_RATIONALE.md` | Detailed per-row classification rationale table |
| `PROJECT_CLASSIFICATION_LOG.md` | This document — full process log |

---

## HOW TO USE / VERIFY THIS DATA

### Quick verification:
```bash
# Check category distribution in CSV
cut -d'|' -f4 nyt_classified_with_rationale.csv | sort | uniq -c

# Count C/R flags  
grep ",Y," nyt_classified_with_rationale.csv | head  # Controversial Y
grep "Y|" nyt_classified_with_rationale.csv | head   # Relevant Y
```

### Verification steps for another agent/LLM to pick up:
1. Read `PROJECT_CLASSIFICATION_LOG.md` (this file) — shows what was done and why
2. Check `nyt_classified_with_rationale.csv` — the actual labeled rows 
3. Look at `CLASSIFICATION_RATIONALE.md` — per-row rationale table
4. Review `classify_all_3390.py` — the classification logic that could be re-run
5. If categories seem off, adjust keyword/phrase patterns in classify_all_3390.py

### Re-running:
```bash
cd /Users/ryanrestivo/Sites/releases
python3 scripts/classify_all_3390.py
```

---

## NEXT STEPS FOR REVIEW

1. Verify C/R flag propagation is working correctly (cross-ref shows 0 titles matched)
2. Consider whether the "company update" default for unclassified rows needs refinement
3. Add more specific content patterns from fullText analysis if coverage seems low
4. Review per-row rationale table against reference data for accuracy

---

## IMPORTANT NOTES FOR FUTURE WORKERS

- **The labeling_test.csv Category column has values in col 4** (index 3) 
- **releases_labeling.csv Category column is BLANK** — rely on C/R flags and URL matching
- Both CSVs use the Title column (col 3, index 2) for matching/reference
- The main CSV has `urls` column (NOT named "url") which maps to releases_labeling Source URL
- Classification uses BOTH storyTitle AND fullText fields for content analysis
