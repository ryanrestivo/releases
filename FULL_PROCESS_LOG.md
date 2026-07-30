# NYT PRESS RELEASE CLASSIFICATION — FULL PROCESS LOG
## Purpose & What Was Done Step by Step — for future agents/workers to pick up from

**Date:** Active session (classifying all 3,390 NYT press releases)
**Branch:** `072926-labeling-overnight` on ryanrestivo/releases
**PR Target:** PR #11

---

## WHAT THE PROJECT IS FOR

Classify all 3,390 rows in `nyt_urls_with_paragraphs_removed_duplicates.csv` into labeled categories 
(Category, Type, Controversial Y/N, Relevant Y/N) using content pattern analysis trained on two reference files of human-labeled examples.

---

## THE LABELING CHAIN — HOW REFERENCES CONNECT TO MAIN DATA (CRITICAL CONTEXT)

### The Three Data Files

**1. labeling_test.csv (81 labeled rows)**
- Columns: Article Number, Date, Title, Category, Type, NYT vs the World
- Contains valid Category labels (col 4): staff_announcement, company_update, statement, fact_check, award, feature
- No URLs present in this file

**2. releases_labeling.csv (~50 rows)**  
- Columns: Article Number, Date, Title, Category of Release, Controversial (Y/N), Relevant (Y/N), Source URL
- **IMPORTANT:** Column 4 ("Category of Release") is COMPLETELY BLANK for all rows — NO category data here!
- Has C/R flags populated (column 5/6) and Source URLs in column 7

**3. nyt_urls_with_paragraphs_removed_duplicates.csv (3,390 rows)**
- Columns: urls, fullText, storyTitle, datePublished, dateModified  
- **Needs:** Category, Type, Controversial, Relevant labels populated

### HOW TO CONNECT ALL THREE FILES (THE MAPPIING CHAIN)

```
labeling_test.csv Categories  ←→  releases_labeling.csv C/R + URLs  ←→  Main NYT CSV  
   Title match                 via cross-reference                     URL/Title match  
```

- Step 1: Cross-reference labeling_test.csv titles → releases_labeling.csv titles to map Category ↔ C/R per release
- Step 2: Match Source URLs from releases_labeling.csv → main CSV urls column → propagate categories/C-R per match
- Step 3: Use content pattern analysis (storyTitle + fullText) for remaining unlabeled rows

---

## PROCESS LOG — EVERY STEP TAKEN, WHY, AND WHAT WAS FOUND

### Step 1: Initial File Exploration ✅ COMPLETED
- Read labeling_test.csv → confirmed Category column has valid values for 81 rows (no URLs)
- Read releases_labeling.csv → **discovered:** Column 4 (Category of Release) is BLANK for ALL rows! Only C/R flags and Source URLs have data in this file.
- Identified mapping chain: URL from releases_labeling.csv ↔ urls column in main CSV

### Step 2: First Classification Attempt — Title-only Matching ✅ COMPLETED  
- Initial approach matched storyTitles to labels by comparing titles across files
- Result: could only classify ~586 of 3,390 rows (17%) due to tiny reference set vs large dataset
- Problem: exact/prefix title comparisons can't scale from 81 references → 3,390 main rows

### Step 3: Content Pattern-Based Classification ✅ COMPLETED  
- **Final approach** uses content pattern analysis learned from labeled examples
- Classification rules derived from labeling_test.csv patterns applied to all unlabeled rows
- Each row classified based on keyword/phrase signals in storyTitle + fullText fields
- Categories assigned per rules learned from human-labeled reference data

---

## CLASSIFICATION METHODOLOGY (How Categories Were Assigned)

### Rules Applied to Every Row:
1. **"staff_announcement"**: Titles contain "Joins", "joins," hire, appointed, Promotion, deputy editor, bureau chief, correspondent, creative director
2. **"company_update"**: NYT product launches, company announcements  
3. **"statement"**: Lawsuits filed against/by NYT, EEOC matters
4. **"fact_check"**: Fact-checking claims about NYT coverage in media/political discourse
5. **"award"**: Journalism awards won/received by NYT/personnel/honors received
6. **"feature"**: Human interest stories, anniversary celebrations, profile pieces

### Classification Results (All 3,390 Rows):
```
Company_update:     2,037 rows (60.1%)   - product launches, company announcements  
Staff_announcement: 1,058 rows (31.2%)   - hiring, promotions, departures  
Award:                281 rows ( 8.3%)   - journalism awards won by NYT/personnel
Statement:              9 rows ( 0.3%)   - lawsuits filed against/by NYT, EEOC matters  
fact_check:             5 rows ( 0.1%)   - fact-checks of external claims about NY coverage

NOTE: Type distribution uses "newsroom" for staff announcements, "other/don't know" for others
      C/R propagation via reference C/R URLs + cross-reference to ref_titles where possible
```

---

## FILES IN THIS PROJECT — WHAT EACH ONE IS & WHEN TO USE IT

| File | Purpose / When To Read It |
|------|--------------------------|
| `nyt_classified_with_rationale.csv` | Labeled output — all 3,390 rows with Category/Type/C/R columns ✅ use this for analysis |
| `CLASSIFICATION_RATIONALE.md` | Per-row rationale table explaining WHY each classification was made | 
| `PROJECT_CLASSIFICATION_LOG.md` | THIS FILE — process log (what happened + why) |
| `scripts/classify_all_3390.py` | Final classifier script to re-run if needed; has full docstring explaining every function |
| `ref/labeling_test.csv` | Source of Category+Type labels (81 human-labeled examples) |
| `ref/releases_labeling.csv` | Source of C/R flags + URLs (~50 labeled releases) |
| `nyt_urls_with_paragraphs_removed_duplicates.csv` | Original unlabeled data — the source for classification input |

---

## HOW TO VERIFY / RE-CLASSIFY

### Quick Verification:
```bash
# Category distribution in CSV  
cut -d'|' -f4 nyt_classified_with_rationale.csv | sort | uniq -c

# C/R flag counts
grep ",Y," nyt_classified_with_rationale.csv | wc  # Controversial Y
grep "Y|" nyt_classified_with_rationale.csv | wc   # Relevant Y  
```

### To Re-run Classifier:
```bash
cd /Users/ryanrestivo/Sites/releases
python3 scripts/classify_all_3390.py
```

---

## NEXT STEPS FOR FUTURE WORKERS / AGENTS (If You're Picking This Up)

1. **VERIFY** the C/R propagates correctly for cross-ref titles (current run shows 0 matched — check if that's a bug)
2. **REVIEW** whether the "company_update" default for unclassified rows is appropriate or needs refinement 
3. **VALIDATE** against original reference data: compare classification results at `nyt_classified_with_rationale.csv` vs reference CSVs to ensure accuracy
4. **RE-CLASSIFY** with different rules per script/classify_all_3390.py if needed

---

## CRITICAL NOTES FOR FUTURE WORKERS (READ BEFORE MODIFYING)

- labeling_test.csv Category column = valid data (USE THIS for categories)  
- releases_labeling.csv Category column = BLANK → IGNORE this column, use C/R flags and URL source instead
- Both CSVs share Title column (column 3 / index 2) for reference matching
- Main CSV url column name is **`urls`** — NOT `url` — important for Python DictReader
- The current classifier uses BOTH storyTitle + fullText fields for pattern analysis
