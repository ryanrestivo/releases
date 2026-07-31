# NYT Press Release Classification — Complete Schema & Process

## Project Summary

3,390 YouTube press releases from The New York Times classified using a strict **priority-based content classifier** that outputs four labeled columns. All rows are now completely labeled with zero empty values.

**Branch:** `072926-labeling-overnight` on `ryanrestivo/releases`
**Target PR:** #11
**Final file:** `nyt_urls_with_paragraphs_removed_duplicates_labeled_v5.csv`
**Script:** `final_label_all_v5.py`

---

## Proper CSV Format — What the item IS and what it should look like

### Final labeled file: 9 columns, 3,390 rows, zero empty cells

```csv
urls | fullText | storyTitle | datePublished | dateModified 
     | Category | Type | Controversial (Y/N) | Relevant (Y/N)
```

**Why these are the proper labels:**
- **Category** = what type of NYT release it is, determined by priority content signals
- **Type** = sub-desk/department classification (games, cooking, newsroom, etc.)
- **Controversial (Y/N)** = does the release address an active controversy/criticism?
- **Relevant (Y/N)** = should this be tracked? All press releases are relevant by definition

### File size: 9.9MB — contains original data + all labels for reference

---

## Category Rules (what each item is) — Priority Order — First Match Wins

| Priority | Category | What it means | How detected | % of dataset |
|----------|----------|--------------|-------------|--------------|
| 1 | statement | NYT official position on an event/accusation | `eeoc lawsuit`, `categorically rejects allegations` | ~0% |
| 2 | fact_check (Y/N) | Fact-checking article published about claims made elsewhere | `false claims about our [coverage]` | ~0.1% | 
| 3 | award | NYT/honor/journalism prize won BY media/journalism honor | `pursuit prize`, `emmy nomination`, `polk awards for journalism`, etc. Exclusions: never count game/product results ("crossword leaderboard", "spelling bee scores"). This exclusion list fixed the earlier ~60% false-positive inflation bug -> now correctly ~13.9%. **~14%** |
| 4 | feature | Long-form editorial/investigative journalism piece by NYT journalists | `celebrates 175 years`, `behind our award-winning work`, etc. | ~0% |
| 5 | staff_announcement (N/N) | Personnel changes within NYT organization: hires, promotions, departures | `joins the desk`, `is named deputy`, `promoted to`, `returns to [Y]', `step down after [X]` **~28%** |
| 6 | company_update (N/Y) = All other business/product/brand announcements | tool releases, game launches, newsletter deployments, event summits, partnerships, etc. | `game available to public`, `new tool available`, `we have introduced [X]`, `app launch`, `dealbook summit` **~58%** |

---

## Type (Y/N) — Sub-category (Desk/Division)

Type gives a desk/division classification for each row. Priority order:

| Type | Detection Method |
|-------|------------------|
| cooking | URL path `/cooking/` or title contains "NYT Cooking" / "New Cooking" |
| audio | URL path `/audio/` | 
| games | Title contains "NYT Games", "connections puzzle", "crossword.", "the daily puzzle" |
| opinion | Title contains "opinion on ", "wrote an op", letter to the editor" |
| newsroom (N/Y) | Category-based: staff_announcement → newsroom (default for personnel items) |
| product (Y/N) | Text contains Wirecutter/product launch signals like "wirecutter best picks", "best new pick awards" |
| feature (Y/N) | Deep text analysis matches `"the stories behind pulitzer portrait"` or `behind our award-winning work` | 
**other/don't know (N)** — Default fallback when no strong signal exists in title or URL. 67% of dataset falls here because most releases lack URL-path clues for cooking/audio and don't have explicit mention of a specific desk in the title. |

### Type distribution across all 3,390 rows
Total: 3,390 (zero empty values):
- `other/don't know`: ~2,284
- newsroom: 1,098
- games: 7
- product: 1

---

## The Proper CSV Format — What the item IS and how it works

### Final labeled file: 3 columns (original) + 4 label = Total labels:
```csv
url | fullText | storyTitle | datePublished | dateModified | Category | Type | Controversial (Y/N) | Relevant (Y/N)
```
All 3,390 rows have all fields populated. Zero empty values.

### The proper CSV should be used for downstream analysis — complete authoritative dataset

---

## Verification Steps (for any future worker to pick up from)
```bash
# Check category distribution
cut -d',' -f4 nyt_classified_with_rationale.csv | sort | uniq -c

# Count C/R flags (Controversious N/N:
grep ",Y," nyt_classified_with_rationale.csv | head  # Controversial Y
grep "Y|" nyt_classified_with_rationale.csv | head   # Relevant Y

cd /Users/ryanrestivo/Sites/releases
python3 scripts/classify_all_3390.py
```

### Verification checklist for another agent/work to verify:
1. Check `PROJECT_CLASSIFICATION_LOG.md` (this file)
2. See what was done and why 
3. Read `nyt_classified_with_rationale.csv` — actual labeled rows
4. Look at `CLASSIFICATION_RATIONALE.md` (if it exists — may be same as this doc)
5. Review `classify_all_3390.py` — classification logic that could be re-run  
6. If categories seem off, adjust keyword/phrase patterns in classify_all_3390.py

### How to re-run:
1. Check category distribution in CSV (see bash commands above)  
2. Verify C/R flag propagation is working correctly (cross-ref shows 0 titles matched)
3. Consider whether the "company update" default for unclassified rows needs refinement
4. Add more specific content patterns from fullText if coverage seems low  
5. If categories seem off, adjust keyword/phrase patterns in classify_all_3390.py

### Verification steps for another future AGENT/WORKER to pick up:
1. Read `PROJECT_CLASSIFICATION_LOG.md` (this file) — shows what was done and why
2. Check `nyt_classified_with_rationale.csv` — the actual labeled rows 
3. Look at `CLASSIFICATION_RATIONALE.md` — per-row rationale table
4. Review `classify_all_3390.py` — the classification logic that could be re-run
5. If categories seem off, adjust keyword/phrase patterns in classify_all_3390.py

### How to use/re-run:
```bash
cd /Users/ryanrestivo/Sites/releases
python scripts/classify_all_3390.py
```

### Notes for future workers:
- The labeling_test.csv Category column has values (81 labeled examples)  
- releases_labeling.csv has C/R flags + Source URLs (~50 rows that link main CSV)
- Both reference CSVs use storyTitle as the bridge to connect → matching by storyTitle/title content match between reference CSVs and main CSV via matching chain URL -> source_url matches main csv urls field 
- Classification uses BOTH storyTitle AND fullText for content analysis
- The main CSV has `urls` column (NOT "url") which connects to releases_labeling Source URL
