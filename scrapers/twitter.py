from patchright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import re
import random
import time
from config import COOKIES, CHROME_ARGS, TWITTER_SESSION, CHECKPOINT_INTERVAL
from urllib.parse import urljoin
import uuid
from utils import is_valid_text, is_english, contains_keyword, save_checkpoint, load_checkpoint, remove_checkpoint, SESSION_DIR
from logger import setup_logger

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

def get_tweet_id_and_url(tweet_element):
    link = tweet_element.find("a", {"href": re.compile(r'/status/')})
    tweet_id = link["href"].split('/')[-1] if link else None
    url = urljoin("https://x.com", link["href"]) if link else None
    return tweet_id, url

def extract_tweet_data(article):
    tweet_id, url = get_tweet_id_and_url(article)
    
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

def scrape_tweets(keyword, target_count):
    logger = setup_logger("twitter", SESSION_DIR)
    logger.info(f"\n{'='*50}")
    logger.info(f"Starting Twitter scrape for: {keyword}")
    logger.info(f"Target count: {target_count}")
    logger.info(f"{'='*50}\n")

    # load existing progress if any
    results, seen_ids = load_checkpoint(keyword, "twitter")
    if len(results) >= target_count:
        logger.info(f"Loaded {len(results)} existing tweets from checkpoint")
        return results[:target_count]

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=TWITTER_SESSION,
            headless=False,
            args=CHROME_ARGS,
        )
        browser.add_cookies(COOKIES)
        page = browser.new_page()
        page.goto(f"https://x.com/search?q={keyword}&f=live")
        
        try:
            consecutive_empty = 0
            max_empty = 15
            refresh_count = 0
            max_refreshes = 5
            
            while len(results) < target_count and refresh_count <= max_refreshes:
                scroll_dist = random.randint(8000, 18000) + random.gauss(500, 200)
                page.mouse.wheel(0, scroll_dist)
                sleep_time = random.uniform(0.9, 1.7) + random.gauss(0.5, 0.2)
                logger.debug(f"Scrolled {scroll_dist}px, sleeping {sleep_time:.2f}s")
                time.sleep(sleep_time)
                
                try:
                    html = page.content()
                    soup = BeautifulSoup(html, 'html.parser')
                    articles = soup.find_all('article')
                    logger.debug(f"Found {len(articles)} articles in current view")

                    new_results = []
                    for article in articles:
                        tweet_id, _ = get_tweet_id_and_url(article)
                        if not tweet_id:
                            logger.debug("Article missing tweet ID")
                            continue
                            
                        if tweet_id in seen_ids:
                            logger.debug(f"Skipping duplicate tweet: {tweet_id}")
                            continue
                        
                        if not should_keep_tweet(article, keyword):
                            logger.debug(f"Rejected tweet {tweet_id} - validation failed")
                            continue
                        
                        tweet_data = extract_tweet_data(article)
                        seen_ids.add(tweet_id)
                        new_results.append(tweet_data)
                        logger.debug(f"Collected tweet: {tweet_id}")

                    if new_results:
                        results.extend(new_results)
                        consecutive_empty = 0
                        logger.info(f"Added {len(new_results)} tweets (Total: {len(results)})")
                        
                        if len(results) % CHECKPOINT_INTERVAL == 0:
                            save_checkpoint(keyword, "twitter", results, seen_ids)
                            logger.info(f"Checkpoint saved at {len(results)} tweets")
                    else:
                        consecutive_empty += 1
                        logger.warning(f"Empty batch ({consecutive_empty}/{max_empty})")

                except Exception as e:
                    logger.error(f"Content processing failed: {str(e)}")

                # handle page refreshing
                if consecutive_empty >= max_empty:
                    if refresh_count < max_refreshes:
                        refresh_count += 1
                        logger.warning(f"Attempting refresh ({refresh_count}/{max_refreshes})")
                        page.reload()
                        time.sleep(3)
                        consecutive_empty = 0
                    else:
                        logger.error("Max refresh attempts reached")
                        break

            if len(results) >= target_count:
                logger.info(f"Successfully collected {len(results)} tweets")
            else:
                logger.warning(f"Stopped early at {len(results)} tweets")

        except Exception as e:
            logger.error(f"Scraping failed: {str(e)}")

        finally:
            save_checkpoint(keyword, "twitter", results, seen_ids)
            browser.close()

        if len(results) >= target_count:
            remove_checkpoint(keyword, "twitter")
            logger.info("Checkpoint removed - collection complete")

        return results[:target_count]

if __name__ == "__main__":
    keyword = "slay"
    tweet_num = 5
    tweets = scrape_tweets(keyword, tweet_num)
    for tweet in tweets:
        print(tweet)