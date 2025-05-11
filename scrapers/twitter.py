from patchright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import re
import random
import time
from config import COOKIES, CHROME_ARGS, TWITTER_SESSION
from urllib.parse import urljoin
import uuid
from utils import is_valid_text, is_english, contains_keyword

def should_keep_tweet(tweet_element, keyword):
    text_div = tweet_element.find("div", {"data-testid": "tweetText"})
    if not text_div:
        return False
        
    tweet_text = ' '.join([span.text for span in text_div.find_all("span")])
    return (
        contains_keyword(tweet_text, keyword) and
        is_valid_text(tweet_text) and
        is_english(tweet_text)
    )

def extract_tweet_data(article):
    link = article.find("a", {"href": re.compile(r'/status/')})
    tweet_id = link["href"].split('/')[-1] if link else None
    url = urljoin("https://x.com", link["href"]) if link else None
    
    time_tag = article.find("time")
    created_at = time_tag["datetime"] if (time_tag and "datetime" in time_tag.attrs) else None

    text = ' '.join([
            span.text 
            for span in article.find("div", {"data-testid": "tweetText"})
        ]) if article.find("div", {"data-testid": "tweetText"}) else ""
    
    username = (article.find("div", {"data-testid": "User-Name"})) \
                .find("a", href=re.compile(r'^/')) \
                .text.strip('@') if article.find("div", {"data-testid": "User-Name"}) else None

    return {
        "uuid": str(uuid.uuid4()),
        "id": tweet_id,
        "text": text,
        "url": url,
        "created_at": created_at,
        "username": username,
    }

def scrape_tweets(keyword, tweet_num):
    link = f"https://x.com/search?q={keyword}&f=live&src=typed_query"

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=TWITTER_SESSION,
            headless=False,
            args=CHROME_ARGS,
        )
        browser.add_cookies(COOKIES)
        page = browser.new_page()
        page.goto(link)
        page.wait_for_selector("article", timeout=15000)

        seen_urls = set()
        results = [] 
        last_html = ""
        
        while len(results) < tweet_num:
            page.mouse.wheel(
                    0, 
                    random.randint(8000, 12000) + 
                    random.gauss(500, 200)
                )
            time.sleep(random.uniform(0.9, 1.2))

            current_html = page.content()
            if current_html == last_html:
                continue

            soup = BeautifulSoup(current_html, "html.parser")
            articles = soup.find_all("article")
            
            for article in articles:
                if not should_keep_tweet(article, keyword):
                    continue
                    
                tweet_data = extract_tweet_data(article)

                if tweet_data["url"] and tweet_data["url"] not in seen_urls:
                    seen_urls.add(tweet_data["url"])
                    results.append(tweet_data)
                    print(f"Collected {len(results)}/{tweet_num}")
                    
            last_html = current_html
        
    return results[:tweet_num]

if __name__ == "__main__":
    keyword = "slay"
    tweet_num = 5
    tweets = scrape_tweets(keyword, tweet_num)
    for tweet in tweets:
        print(tweet)