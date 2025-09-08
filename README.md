# releases
This is going to compile and run to get NYT releases


## Why do this? 
- Source: "https://drnews.substack.com/p/claude-youre-going-to-blow-us-all?utm_source=post-email-title&publication_id=1543102&post_id=154501431&utm_campaign=email-post-title&isFreemail=true&r=qj5c&triedRedirect=true
    "I was able to get the first 25 stories scraped, but couldn’t do anything historic."

    Let's fix that... Using the inspector on this page, found the AJAX calls made, use these to fetch the data

    But that was v1, then this outlet redesigned their press release page in July 2025, maybe thinking ajax calls are out of style. So built a new parser (a much easier one), to pull these.