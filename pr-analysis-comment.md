## Analysis of Labeled Dataset (3,390 rows)

Full breakdown in `ANALYSIS.md` on this branch. Here's a scannable summary:

---

### Category Distribution
- **staff announcement**: 3,201 (94.4%) — personnel moves dominate
- **award**: 129 (3.8%) — Pulitzer, Emmy, Polk winners matched by proper nouns
- **company update**: 44 (1.3%) — product launches, mostly The Athletic
- **fact check / feature / statement**: 16 total (<0.5%) — low-volume edge cases

### Type Distribution
- **newsroom**: 2,024 (59.7%) — desk/editorial assignments and award recipients
- **other/don't know**: 833 (24.6%) ⚠️ Largest gap — short fullTexts lacking department signals
- Opinion (179), Cooking (107), Audio (104), Games (65)

### Cross-tab Highlights
- Awards → 66% newsroom-type, 25% unclassified → prizes go to journalism desks
- Company updates → 55% The Athletic (acquisition drove volume spike)
- Staff splits: 60% newsroom → 30% other/don't know → rest scattered across departments

### Controversial Analysis (34 Y / 3,356 N — ~1%)
- **Only `statement` category produces Y flags** (legal/gov disputes)
- Zero controversial items in awards, company updates, or staff categories
- All Y entries: NYT vs Pentagon, NYT vs Perplexity AI, CPJ press freedom disputes

### Relevant Analysis (624 Y / 2,766 N — ~18%)
- Driven by executive titles + named executives (Sulzberger, Kopit Levien)
- Strategic announcements ("core mission," "future of journalism") also flag Y
- ~80% of releases are operationally neutral

### Timeline
- **Span**: Oct 2013 → July 2026 (152 months, ~13 years)
- **Peak month**: May 2021 (64 items) — Wordle acquisition period
- **Average**: 22.3/month, escalating to 38–45/month by mid-2020s

### Classification Confidence
| Category | Confidence | Method | Gap |
|----------|-----------:|--------|-----|
| Award | HIGH (~47 cross-matched) | Proper nouns + URL slug | ~53% pattern-only |
| Statement | MEDIUM-HIGH | 2 items, both VERIFIED against REF2 Y patterns | None (small sample) |
| Company update | MEDIUM (~80%) | Pattern matching | Athletic/staff boundary overlap |
| Staff announcement | MEDIUM-LOW (~70% cross-mixed) | Default fallback | 529 in "other/don't know" — needs broader desk-pattern rules |

> ⚠️ **Biggest gap**: 833 rows classified `other/don't know` because fullText <300 chars lacks department signals. These are likely valid staff/company items but unclassifiable with current rules. Adding broad-signal keywords could reduce this rate significantly.

---

*Full analysis in `ANALYSIS.md`: cross-tabs, monthly tables (>150 rows), title length stats per category, URL slug patterns, keyword analysis, confidence matrix, improvement recommendations.*
