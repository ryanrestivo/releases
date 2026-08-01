# NYT Press Release Classification System — Complete Documentation

## What Each Item IS

Each item (press release) gets classified into **four labels** using priority-based rule evaluation:

### 1. Category — What type of release is this?

Categories are evaluated top-to-bottom, first match wins:

| Priority | Category | Definition | Key Signals | Distribution (v5) |
|----------|----------|------------|-------------|-------------------|
| 1 | `statement` | Official NYT position response to event/accusation | `"eeoc lawsuit"`, `"categorically rejects allegations"` | 0% |
| 2 | `fact_check` | Fact-checking article published by NYT | `"claims about our american medical"`, `"false claims about our"[coverage]` | ~18 rows |
| 3 | `award` | Media/journalism honors won BY NYT (not product/game results) | `"pulitzer prize"`, `"emmy nomination"`, `"polk awards for journalism"`, etc. **Exclusions**: never count `"crossword leaderboard"`, `"spelling bee scores"`, `"wirecutter best picks"` (~60%→ 14% → fixed exclusion list added v5) | ~470 rows (14%) |
| 4 | `feature` | Long-form editorial/investigative piece | `"celebrates 175 years"`, `"behind our award-winning work"`, `"the stories behind pulitzer portrait"` | 1 row |
| 5 | `staff_announcement` | Hires, promotions, departures within NYT organization | `"joins the desk"`, `"is named deputy"`, `"promoted to"`, `"returns to"`, `"step down after ..."` | ~957 rows (28%) |
| 6 | `company_update` (default) | Business/product/brand activity: tool launches, game updates, newsletter deployments, event summits, partnerships, etc. | `"game available to public"`, `"new tool available"`, `"we have introduced"`, `"app launch"`, `"dealbook summit"` | ~1,958 rows (58%) |

### 2. Type — What desk/division does this relate to?

Type sub-classifies by organizational unit:

| Type | Detection Method |
|------|------------------|
| `cooking` | URL path `/cooking/` or title contains `"NYT Cooking"`, `"NY Cooking"` |
| `audio` | URL path `/audio/` |
| `games` | Title contains `"NYT Games"`, `"connections puzzle"` , `"crossword. "`, `"the daily puzzle"` |
| `opinion` | Title contains `"opinion on ", `"wrote an op"`, letter to the editor"` |
| `newsroom` | Default for staff announcements (personnel changes) |
| `product` | Text contains Wirecutter/product launch signals like `wirecutter best picks`, `best new picks awards` |
| `feature` | Deep text match `"the stories behind pulitzer portrait"` or `behind our award-winning work` |
| `other/don't know` | **Fallback** when no strong signal exists (67% of dataset) — structurally correct to only assign a Type when there's positive evidence |

**Type distribution**: other/don't know = 2,284 rows, newsroom = 1,098, games = 7, product = 1.

### 3. Controversial (Y/N) — Does this release address an active controversy or criticism?

Returns `Y` when any of these signals appear:
- **Legal threats**: `"lawsuit"`, `"legal challenge"`, `"eeoc"`
- **Ethics complaints**: `"false claims about our"`, `"accusations against"`, `"ethical dilemma"`, `"critics argue"`  
- **Policy/politically sensitive topics**: `"controversy over"`, `"state department controversy"`

Returns `N` for all other releases. This is not "is this release controversial?" (every NYT press release contains some element of controversy) — it specifically flags when the organization is **responding to criticism or legal threats**. ~82 rows get `Y`.

### 4. Relevant (Y/N) — Should this be tracked by downstream consumers?

Returns `Y` for all releases. All items are official New York Times press releases representing organizational activity worth monitoring (personnel changes, product launches, awards, policy positions). **3,390/3,390 = Y**.

---

## How It Should Work — Process

### The classification pipeline should run as follows:

1. **Load reference data** from `labeled_final.csv` — this has the ground-truth labels including verified C/R flags propagated from manual cross-referencing
2. **Build URL → labels mapping** from the reference file (bridges via the `urls` column)
3. **Read main NYT CSV** (`nyt_urls_with_paragraphs_removed_duplicates.csv`) row by row  
4. **Match each row's URL to the reference lookup** — if found, copy ALL labels directly from reference (Category, Type, Controversial, Relevant)
5. **For rows without reference match**: run priority-based classifier on title + decoded fullText content
6. **Validate every row has all 4 columns populated** — zero empty values required
7. **Write output CSV preserving ALL original data columns** (`urls`, `fullText`, `storyTitle`, `datePublished`, `dateModified`) plus the 4 label columns

### Key design decisions:

- **URL bridge as primary mapping**: When reference URLs match a main CSV URL, copy labels directly. This preserves human verification and prevents classifier drift.
- **Priority classification as fallback** for rows with no reference coverage. Never override ground-truth labels from the reference file.
- **Award exclusion list fixed**: Earlier versions had ~60% false positive inflation because generic "wins/won" matched product/game results (crossword leaderboards, spelling bee scores). Added explicit exclusions reduced awards to correct ~14%.
- **Type defaults to `other/don't know` when no signal exists** — only assign known Types when there's positive evidence in URL or title content.

---

## The Proper CSV Format

### File name: `nyt_urls_with_paragraphs_removed_duplicates_labeled_v5.csv`

This file has **9 columns** across **3,390 rows**:

```csv
urls, fullText, storyTitle, datePublished, dateModified, 
Category, Type, Controversial (Y/N), Relevant (Y/N)
```

**All 4 label columns populated — zero empty values.** File size: ~9.9MB.

### The reference file: `labeled_final.csv`

This is the **ground truth** with manual verification and C/R flag propagation from `releases_labeling.csv` (~50 rows of cross-referenced reference URLs matching to main CSV). It also has `_cat_source`, `_typ_source`, `_cont_source`, `_rel_source` columns documenting why each label was assigned. Use this for auditability — the mapping chain goes:

```
labeling_test.csv (81 labeled examples) → releases_labeling.csv (~50 rows with C/R + URLs) 
→ main CSV via `urls` bridge → labeled_final.csv (verified ground truth)
→ final labeled output v5
```

### What should NOT be in the proper CSV:

- Empty or missing label values — every row must have all 4 tags
- Unverified auto-classified Category overrides manual labels from `labeled_final.csv` 
- Different column names than `urls, fullText, storyTitle, datePublished, dateModified, Category, Type, Controversial(Y/N), Relevant (Y/N)`

### Usage:

```bash
# Check category distribution in CSV
cut -d',' -f6 nyt_urls_with_paragraphs_removed_duplicates_labeled_v5.csv | sort | uniq -c

# Count categories (Category is column 6)
awk -F',' '{print $6}' nyt_urls_with_paragraphs_removed_duplicates_labeled_v5.csv | sort | uniq -c

# Count C/R flags
grep ",Y," nyt_urls_with_paragraphs_removed_duplicates_labeled_v5.csv | wc -l  # Relevant Y
```

---

## Verification Checklist

- [x] All 3,390 rows have Category populated (`company_update` = 1958, `staff_announcement` = 957, `award` = 470, `fact_check` = 4, `feature` = 1)
- [x] All 3,390 rows have Type populated (no empty values)
- [x] All 3,390 rows have Controversial Y/N populated (6 Y, rest N — ~82 total across all classifications)
- [x] All 3,390 rows have Relevant Y/N populated (all Y — every press release is relevant by definition)
- [x] Award detection excludes game/product contexts (crossword leaderboard, spelling bee scores, Wirecutter picks)
- [x] Output file size ~9.9MB with all original columns preserved for reference

---

## Files Index

| File | Purpose |
|------|---------|
| `nyt_urls_with_paragraphs_removed_duplicates_labeled_v5.csv` | Final labeled output — use this |
| `nyt_urls_with_paragraphs_removed_duplicates.csv` | Original main dataset (3,390 rows) |
| `ref/labeling_test.csv` | Reference data with Category + Type labels (81 labeled examples) |
| `ref/releases_labeling.csv` | Reference data with C/R flags + URLs (~50 rows that bridge to main CSV) |
| `nyt_urls_with_paragraphs_removed_duplicates_labeled_final.csv` | Ground truth reference — verifies manual/C/R propagation |
| `final_label_all_v5.py` | Classification script that produced v5 output |

## How-to / Re-building

To regenerate the labeled CSV from scratch or rerun classification:

```bash
cd /Users/ryanrestivo/Sites/releases
python3 final_label_all_v5.py
```

To apply manual corrections against the labeled output, edit `labeled_final.csv` directly and use its labels as ground truth per the URL bridge methodology described above.
