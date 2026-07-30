#!/usr/bin/env python3
"""Complete labeling pipeline for NYT press releases."""
import csv, re, os, sys
from collections import defaultdict

def norm(s):
    if not s: return ""
    s = str(s).lower().strip()
    s = re.sub(r'[^\w\s]', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()

def has_kw(text, keywords):
    ttext = (text or '').lower()
    for kw in keywords:
        if kw.lower() in ttext:
            return True
    return False

REF_CAT = {}
with open('/Users/ryanrestivo/Downloads/labeling_test.csv', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f, skipinitialspace=True)
    for row in reader:
        title = (row.get('Title') or '').strip()
        if not title: continue
        key = norm(title)
        REF_CAT[key] = {
            'cat': (row.get('Category') or '').strip(),
            'typ': (row.get('Type') or '').strip()
        }

REF_CR = {}
with open('/Users/ryanrestivo/Downloads/releases_labeling.csv', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f, skipinitialspace=True)
    for row in reader:
        title = (row.get('Title') or '').strip()
        if not title: continue
        key = norm(title)
        c_str = (row.get('Controversial (Y/N)') or 'N').strip().upper()
        r_str = (row.get('Relevant (Y/N)') or 'N').strip().upper()  
        REF_CR[key] = {
            'c': 'Y' if c_str == 'Y' else 'N',
            'r': 'Y' if r_str == 'Y' else 'N'
        }

with open('/Users/ryanrestivo/Sites/releases/nyt_urls_with_paragraphs_removed_duplicates.csv', encoding='utf-8-sig') as f:
    MAIN = list(csv.DictReader(f))

print('Loaded refs: Cat.Type=%d C/R=%d' % (len(REF_CAT), len(REF_CR)))
print('Main rows to classify: %d\n' % len(MAIN))

# Classify all rows using learned taxonomy from ref pattern analysis

def find_ref_match(story_norm):
    """Find exact reference match for normalized title."""
    for ref_t in REF_CAT:
        if story_norm == ref_t or (ref_t and (story_norm in ref_t or ref_t in story_norm)):
            return 'cat', ref_t
    for ref_t in REF_CR:
        if story_norm == ref_t or (ref_t and (story_norm in ref_t or ref_t in story_norm)):
            return 'cr', ref_t
    return None, None

def classify_row(story, fulltext):
    """Classify one NYT press release using learned taxonomy."""
    sn = norm(story) if story else ''
    ft_low = (fulltext or '').lower().replace('  ', ' ')
    
    cat_v = ''
    typ_v = ''
    cont_v = 'N'
    rel_v = 'N'
    src_cat = 'unmatched'
    src_typ = 'unmatched'
    src_cv = 'no_cr_ref'  
    src_rv = 'no_rel_ref'
    
    rtype, rref_t = find_ref_match(sn)
    
    if rtype == 'cat':
        clb = REF_CAT[rref_t]
        cat_v = clb['cat']
        typ_v = clb['typ']
        src_cat = 'exact_cat_' + rref_t[:50].replace(' ', '_')
        src_typ = 'exact_typ_' + rref_t[:50].replace(' ', '_')
        
        cr_m = REF_CR.get(rref_t, None)
        if cr_m:
            cont_v = cr_m['c']
            rel_v = cr_m['r']
            cv_s = 'Y' if cont_v == 'Y' else 'N'
            rv_s = 'Y' if rel_v == 'Y' else 'N'  
            src_cv = 'cr_%s_ref_' % cv_s + rref_t[:30].replace(' ', '_')
            src_rv = 'rel_%s_ref_' % rv_s + rref_t[:30].replace(' ', '_')
        return cat_v, typ_v, cont_v, rel_v, src_cat, src_typ, src_cv, src_rv
    
    # Apply learned patterns from fullText analysis of labeled examples
    if has_kw(ft_low, ['joins', 'joined', 'new hire', 'promoted', 'promotion']):
        cat_v = 'staff_announcement'
        src_cat = 'pattern_staff_hire_keywords'
    elif has_kw(ft_low, ['announces new partnership expansion launch:']):
        cat_v = 'company_update'
        src_cat = 'pattern_business_announcement'  
    elif has_kw(ft_low + story, ['celebrat anniversary special section featured']):
        cat_v = 'feature' 
        src_cat = 'pattern_feature_content'  
    elif has_kw(ft_low + story, ['responds to lawsuit', 'the new york times responds to:']):  
        cont_v = 'Y'
        rel_v = 'Y'
        src_cv = 'controversial_legal_action'  
        src_rv = 'relevant_strategic_impact' 
    elif has_kw(ft_low, ['false claim inaccurate claims about our misinformation']):
        cat_v = 'fact_check'
        cont_v = 'Y'
        rel_v = 'N'
        src_cv = 'controversial_fact_check_misinfo'  
        src_rv = 'relevant_correction_value'
    elif has_kw(ft_low, ['awards recognized won the award honored polk pulitzer prize:']):  
        cat_v = 'award'
        rel_v = 'Y'
        src_cv = 'non_controversial_award'
        src_rv = 'relevant_important_recognition'
    else:  
        cat_v = 'company_update'  # Default most NYT press releases are company updates
        src_cat = 'default_company_update_category' 
    
    # Type classification using learned patterns
    if has_kw(ft_low, ['hard fork daily podcast audio production']):  
        typ_v = 'audio'
        src_typ = 'type_audio_pattern'
    elif has_kw(ft_low, ['opinion the times opinion columnist op-ed:']:
)        typ_v = 'opinion' 
        src_typ = 'type_opinion_pattern'  
    elif has_kw(ft_low, ['desk editor newsroom office news desk national international']):
        typ_v = 'newsroom'  
        src_typ = 'type_newsroom_pattern'
    elif has_kw(ft_low, ['games crossword wordle connections:']:
)        typ_v = 'games'
        src_typ = 'type_games_pattern'
    elif has_kw(ft_low, ['the athletic athletics staff:']):  
        typ_v = 'the athletic'  
        src_typ = 'type_athletic_pattern'
    elif has_kws(ft_lower, ['cooking recipes ny times cooking']): 
        typ_v = 'cooking'  
        src_typ = 'type_cooking_pattern' 
    else:  
        typ_v = "other/don't know"
        src_typ = "type_unk_default_unlabeled_no_matching"

    return cat_v, typ_v, cont_v, rel_v, src_cat, src_typ, src_cv, src_rv


# Classify ALL rows and build output
output_rows = []  
cat_counts = defaultdict(int)  

for idx, row in enumerate(MAIN):
    story_t = (row.get('storyTitle') or '').strip()
    ft_txt = (row.get('fullText') or '')
    
    cv, tv, cov, rov, sc, stp, scov, srov = classify_row(story_t, ft_txt)   
    
    out_row = dict(row)  
    out_row['Category'] = cv 
    out_row['Type'] = tv
    out_row['Controversial (Y/N)'] = cov
    out_row['Relevant (Y/N)'] = rov  
    out_row['_cat_source'] = sc[:200]
    out_row['_type_source'] = stp[:200]  
    out_row['_cont_source'] = scov[:200]
    out_row['_rel_source'] = srov[:200]
    
    output_rows.append(out_row)  
    if cv and 'unlabeled' not in cv:
        cat_counts[cv] += 1
    
    # Print progress every 500 rows  
    if (idx + 1) % 500 == 0 or idx == len(MAIN) - 1:  
        pct = ((idx + 1) / len(MAIN)) * 100.0
        print('Progress: %d/%d (%.1f%% complete)' % (idx + 1, len(MAIN), pct))

# Output labeled CSV 
out_csv_path = '/Users/ryanrestivo/Sites/releases/nyt_urls_with_paragraphs_removed_duplicates_labeled.csv'  
if output_rows and len(output_rows) > 0:
    fieldnames_list = list(output_rows[0].keys())  
    with open(out_csv_path, 'w', newline='', encoding='utf-8-sig') as fout: 
        writer = csv.DictWriter(fout, fieldnames=fieldnames_list)
        writer.writeheader()
        for row_out in output_rows:
            out_vals = {k2: (row_out.get(k2) or '') for k2 in fieldnames_list}
            writer.writerow(out_vals)

print('\nCategory distribution from classification:') 
for cat_s, cnt in sorted(cat_counts.items(), key=lambda x: -x[1]):
    pct = (cnt / len(MAIN)) * 100.0 if 'unlabeled' not in cat_s else 0  
    sys.stderr.write('  %s: %d (%.1f%%)\n' % (cat_s, cnt, pct))

print('\nTotal rows classified: %d/%d (%.1f%%)' % (len([c for c in cat_counts if 'unlabeled' not in c]), len(MAIN), sum(cat_counts.values()) / max(len(MAIN), 1) * 100.0))
print('\nOutput CSV at:')  
print('  %s' % out_csv_path)
