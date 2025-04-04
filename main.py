import requests
import pandas as pd
import json
from bs4 import BeautifulSoup
import os


# https://drnews.substack.com/p/claude-youre-going-to-blow-us-all?utm_source=post-email-title&publication_id=1543102&post_id=154501431&utm_campaign=email-post-title&isFreemail=true&r=qj5c&triedRedirect=true





def get_links():
  """
  how you get all this is to look in the Network tab in Chrome and when you "Load More" it makes this request... which I found page 2...
  When you hit the "Load More" you can see when the request happens (in microseconds) and then find it
   So then assuming pages go in order (because organizing things), I could use a simple loop to query for every one "pretending"
   I'm a browser with these requests.
  """
  link_list = []
  for i in range(0,1000): # assuming 1000 pages of this stuff, which there's clearly not
    url = os.getenv("AJAX")
    print(url)
    headers = json.loads(os.getenv("HEADERS"))
    print(headers)
    cookies = json.loads(os.getenv("HASH"))
    print(cookies)
    data = {
        "action": "filter_posts",
        "filter": "0",
        "page": f"{i}", # turn through the pages of the data
        "post_id": "73",
        "isLoadingMore": "true"
    }
    print(data)
    response = requests.post(url, headers=headers, cookies=cookies, data=data)
    print(response.status_code)
    if response.status_code != 200:
      break
    #print(response.text)
    response_text = response.text
    # use bs4 to parse the page for links
    soup = BeautifulSoup(response_text, 'html.parser')
    for link in soup.find_all('a', href=True):
      link = link['href'].replace('\\', '').replace('"', '')
      link_list.append(link)
      if link == os.getenv("FIRST_RELEASE"):
        print(f"done on page {i}")
        break
  return link_list

def pullstory(url):
  # plus this by adding a lightweight scraper to take each URL and run the story.
  r = requests.get(url)
  soup = BeautifulSoup(r.text, 'html.parser')
  paragraphs = []
  # find any paragraph on the page, then make them one big text box
  for graph in soup.find_all('p'):
    paragraphs.append(graph.text.strip())
  return ' '.join(paragraphs)

if __name__ in "__main__":
    df = pd.DataFrame()
    nyt_links = get_links()
    df['urls'] = pd.Series(nyt_links)
    df['fullText'] = df['urls'].apply(lambda x:pullstory(x))
    df.to_csv('nyt_urls_with_paragraphs.csv',index=False)