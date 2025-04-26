from twitter import scrape_tweets
from reddit import reddit_search

keywords = ["slay", "flex", "lit", "simp"]
amount = 100
for keyword in keywords:
    print(f"Scraping Twitter for keyword: {keyword}")
    scrape_tweets(keyword, amount)
    print(f"Scraping Reddit for keyword: {keyword}")
    reddit_search(keyword, amount)