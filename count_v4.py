import csv

v4 = '/Users/ryanrestivo/Sites/releases/nyt_urls_with_paragraphs_removed_duplicates_labeled_v4.csv'
with open(v4) as f:
    r = csv.DictReader(f)
    rows = list(r)

print('Total rows:', len(rows))
cols = ['Category','Type','Controversial','Relevant']
for c in cols:
    empty=sum(1 for row in rows if (row.get(c,'') or '').strip()=='')
    print(f'{c}: {empty} empty ({empty/len(rows)*100:.1f}%)')

dists={}
for row in csv.DictReader(open(v4)):
    v=row.get('Category','') or 'UNKNOWN'
    dists[v]=dists.get(v,0)+1
print('\nCategory distribution:')
for k,v in sorted(dists.items(), key=lambda x:-x[1]): print(f'  {k}: {v}')

# Check what the original CSV column names are 
orig = '/Users/ryanrestivo/Sites/releases/nyt_urls_with_paragraphs_removed_duplicates.csv'
with open(orig) as f:
    first = csv.DictReader(f).__next__()
print('\nOriginal columns:', list(first.keys()))
