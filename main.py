import requests
import pandas as pd
import json
from bs4 import BeautifulSoup
import os


# "https://drnews.substack.com/p/claude-youre-going-to-blow-us-all?utm_source=post-email-title&publication_id=1543102&post_id=154501431&utm_campaign=email-post-title&isFreemail=true&r=qj5c&triedRedirect=true
# " I was able to get the first 25 stories scraped, but couldn’t do anything historic."
# Let's fix that... Using the inspector on this page, found the AJAX calls made, use these to fetch the data


### NYT Decides to redesign their press releases page in July
### NEW CODE

def get_new_page():
  response = requests.get('https://www.nytco.com/press/all-announcements/')
  response_text = response.text
  soup = BeautifulSoup(response_text, 'html.parser')
  articles = soup.find_all('article', class_='press-post')
  data = pd.DataFrame()
  urls = []
  titles = []
  text = []
  pub_times = []
  mod_time = []
  for article in articles:
      date = article.get('data-date')
      url = article.select_one('.press-text a')['href']
      title = article.select_one('.press-text h4 a span').text.strip()
      urls.append(url)
      titles.append(title)
      z = requests.get(url)
      url_data = BeautifulSoup(z.text, 'html.parser')
      main_content = url_data.find('div', class_='js-content-fade')
      paragraphs = main_content.find_all('p')
      parse_data = BeautifulSoup(z.text, 'lxml')
      meta_tag = parse_data.select_one('meta[property="article:published_time"]')
      if meta_tag:
        published_time = meta_tag.get("content")
        pub_times.append(published_time)
      else:
        pub_times.append(None)
      mod_tag = parse_data.select_one('meta[property="article:modified_time"]')
      if mod_tag:
        modify_time = mod_tag.get("content")
        mod_time.append(modify_time)
      else:
        mod_time.append(None)
      story_text = []
      for i, p in enumerate(paragraphs, 1):
          story_text.append(f"{p.get_text()}")
      text.append(f"{''.join(story_text)}")
  data['urls'] = pd.Series(urls)
  data['fullText'] = pd.Series(text)
  data['storyTitle'] = pd.Series(titles)
  data['datePublished'] = pd.Series(pub_times)
  data['dateModified'] = pd.Series(mod_time)
  return data





### ORIGINAL CODE 

def get_links(last_url):
  """
  how you get all this is to look in the Network tab in Chrome and when you "Load More" it makes this request... which I found page 2...
  When you hit the "Load More" you can see when the request happens (in microseconds) and then find it
   So then assuming pages go in order (because organizing things), I could use a simple loop to query for every one "pretending"
   I'm a browser with these requests.
  """
  link_list = []
  for i in range(0,1000): # assuming 1000 pages of this stuff, which there's clearly not
    url = "https://www.nytco.com/wp/wp-admin/admin-ajax.php"
    headers = json.loads(os.getenv("HEADERS"))
    cookies = json.loads(os.getenv("HASH"))
    data = {
        "action": "filter_posts",
        "filter": "0",
        "page": f"{i}", # turn through the pages of the data
        "post_id": "73",
        "isLoadingMore": "true"
    }
    response = requests.post(url, headers=headers, cookies=cookies, data=data)
    if response.status_code != 200:
      break
    response_text = response.text
    # use bs4 to parse the page for links
    soup = BeautifulSoup(response_text, 'html.parser')
    for link in soup.find_all('a', href=True):
      link = link['href'].replace('\\', '').replace('"', '')
      if link == last_url:
        print(f"done on page {i}")
        break
      else:
        link_list.append(link)
      if link == last_url:
        break
  return link_list

def pullstory(url):
  # plus this by adding a lightweight scraper to take each URL and run the story.
  r = requests.get(url)
  soup = BeautifulSoup(r.text, 'html.parser')
  paragraphs = []
  # find any paragraph on the page, then make them one big text string
  for graph in soup.find_all('p'):
    paragraphs.append(graph.text.strip())
  return ' '.join(paragraphs)

def schemaCrawler(soup):
    return json.loads(soup.find_all("script", type="application/ld+json")[0].contents[0])

def pullSchema(url, itemName):
  r = requests.get(url)
  soup = BeautifulSoup(r.text, 'html.parser')
  try:
    item = schemaCrawler(soup)['@graph'][-1][itemName]
    #print(item)
    if itemName in ['datePublished', 'dateModified']:
      item = pd.to_datetime(item).strftime("%Y-%m-%d %H:%M:%S")
  except:
    item = None
  return item


if __name__ in "__main__":
    df2 = pd.read_csv('nyt_urls_with_paragraphs.csv')
    print(f"{len(df2)} items!")
    last_url = df2.iloc[0]['urls']
    print(last_url)
    df = get_new_page() # fetch all releases from page one
    print(f"{len(df)} new press releases on this run!")
    df3 = pd.concat([df2, df])
    df3 = df3.drop_duplicates() # drop the dupes
    # pump out the new CSV
    df3.sort_values('datePublished',ascending=False).to_csv('nyt_urls_with_paragraphs.csv',index=False)