import csv

v3 = '/Users/ryanrestivo/Sites/releases/nyt_urls_with_paragraphs_removed_duplicates_labeled_v3.csv'
with open(v3) as f:
    r = csv.DictReader(f)
    rows = list(r)

print('Total rows in v3:', len(rows))
cols = ['Category','Type','Controversial','Relevant']
for c in cols:
    empty=sum(1 for row in rows if (row.get(c,'') or '').strip()=='')
    print(f'{c}: {empty} empty ({empty/len(rows)*100:.1f}%)')

# Check column names
print('\nColumns:', list(rows[0].keys()) if rows else 'none')
