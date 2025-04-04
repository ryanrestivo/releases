import requests
import pandas as pd
import json
from bs4 import BeautifulSoup
import os


# "https://drnews.substack.com/p/claude-youre-going-to-blow-us-all?utm_source=post-email-title&publication_id=1543102&post_id=154501431&utm_campaign=email-post-title&isFreemail=true&r=qj5c&triedRedirect=true
# " I was able to get the first 25 stories scraped, but couldn’t do anything historic."
# Let's fix that... Using the inspector on this page, found the AJAX calls made, use these to fetch the data



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
    # wrap this in a try in case no data
    df = pd.DataFrame()
    nyt_links = get_links(last_url)
    df['urls'] = pd.Series(nyt_links)
    df['fullText'] = df['urls'].apply(lambda x:pullstory(x))
    df['storyTitle'] = df['urls'].apply(lambda x:pullSchema(x,'name'))
    df['datePublished'] = df['urls'].apply(lambda x:pullSchema(x,'datePublished'))
    df['dateModified'] = df['urls'].apply(lambda x:pullSchema(x,'dateModified'))
    print(f"{len(df)} new press releases on this run!")
    df3 = pd.concat([df2, df])
    df3.to_csv('nyt_urls_with_paragraphs.csv',index=False)