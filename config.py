from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

AMOUNT = 700
KEYWORDS = {
        "slay": {
            "old": "To kill violently",
            "new": "To have a strong favorable effect; to be remarkably impressive",
        },
        "lit": {
            "old": "Past tense of light",
            "new": "Exciting/awesome, general term of approval",
        },
        "sigma": {
            "old": "Greek letter",
            "new": "Something extremely good/a coolly independent, successful person",
        },
        "karen": {
            "old": "Female name",
            "new": "Someone obnoxious, angry, and entitled",
        },
        "troll": {
            "old": "Mythical creature",
            "new": "Internet user who provokes others online",
        },
        "influencer": {
            "old": "Anyone who exerts influence",
            "new": "A person who generates interest in something by posting about it on social media",
        }
    }

OUTPUT_DIR = Path("output")
TWITTER_SESSION = Path("twitter_session")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
TWITTER_SESSION.mkdir(parents=True, exist_ok=True)

CHECKPOINT_DIR = OUTPUT_DIR / "checkpoints"
CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
CHECKPOINT_INTERVAL = 100

REDDIT_CREDENTIALS = {
    "username": os.getenv("REDDIT_USERNAME"),
    "password": os.getenv("REDDIT_PASSWORD"),
    "user_agent": os.getenv("REDDIT_USER_AGENT"),
    "client_id": os.getenv("REDDIT_CLIENT_ID"),
    "client_secret": os.getenv("REDDIT_CLIENT_SECRET"),
}

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

PROMPT_TEMPLATE = """Classify usage of "{keyword}" in this text as:
- 'old' for meaning: "{old}"
- 'new' for meaning: "{new}"
- 'unknown' if unclear

Text: {text}

Respond with ONLY one word:"""

CHROME_ARGS = [
    "--profile-directory=CustomerProfile",
    "--disable-features=SameSiteByDefaultCookies,CookiesWithoutSameSiteMustBeSecure",
    "--disable-blink-features=AutomationControlled",
    "--force-device-scale-factor=1",
    "--lang=pl-PL",
    "--disable-web-security",
    "--use-fake-ui-for-media-stream",
    "--use-fake-device-for-media-stream",
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
    "--disable-gpu",
    "--disable-webgl",
    "--disable-webrtc",
    "--disable-features=NetworkService,NetworkServiceInProcess",
]

COOKIES = [
    {
      "name": "is_user_logged_in",
      "value": "false",
      "domain": "www.x-kom.pl",
      "path": "/",
      "expires": -1,
      "httpOnly": False,
      "secure": False,
      "sameSite": "Lax"
    },
    {
      "name": "trackingPermissionConsentsValue",
      "value": "%7B%22cookies_analytics%22%3Atrue%2C%22cookies_personalization%22%3Atrue%2C%22cookies_advertisement%22%3Atrue%7D",
      "domain": "www.x-kom.pl",
      "path": "/",
      "expires": 1772412318.075002,
      "httpOnly": False,
      "secure": False,
      "sameSite": "Lax"
    },
    {
      "name": "test_cookie",
      "value": "CheckForPermission",
      "domain": ".doubleclick.net",
      "path": "/",
      "expires": 1740856269.305768,
      "httpOnly": False,
      "secure": True,
      "sameSite": "None"
    },
  ]