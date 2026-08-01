# Labeling Pipeline — Step-by-Step Plan

## STEP 1: Analyze ground truth (labeling_test.csv)
- Parse all ~80 labeled rows (already have the raw content from earlier `read_file`)
- Count category distribution: staff_annoucement, fact check, award, feature, company_update
- Count missing labels
- Collect signal patterns per category

## STEP 2: Build mapping layer
- For each ground truth row in labeling_test.csv, find the matching source release in nyt_urls_with_paragraphs_removed_duplicates.csv by comparing titles (fuzzy match) or Source URLs
- For every matched pair, save the fullText + storyTitle for that labeled item — this gives us REAL SIGNAL PA TTERNS to derive classifiers from

## STEP 3: Build comprehensive classifier
- Using actual patterns extracted from ground truth + full text of matched items, write a full-text classifier that detects all 6 categories using signal lists derived from real data
- Priority chain: statement > fact_check > award > feature > staff_announcement > company_update (default)

## STEP 4: Classify ALL rows in source CSV
- Run the classifier across all ~3,300+ rows of nyt_urls_with_paragraphs_removed_duplicates.csv
- For each item evaluate storyTitle AND fullText for comprehensive signal detection
- Output: labeled CSV with Category, Type, Controversial (Y/N), Relevant (Y/N) columns

## STEP 5: Verify and commit
- Check unlabelled rate (<1% target)
- Commit classifier.py + batch labeling script + labeled output to PR branch
- Push and verify on remote
