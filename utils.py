import re
from langdetect import detect, LangDetectException

def is_valid_text(text: str) -> bool:
    cleaned_text = re.sub(r'http\S+|\n|[^\w\s]', ' ', text, flags=re.IGNORECASE) # Remove URLs
    words = re.findall(r'\b[a-z]+\b', cleaned_text, flags=re.IGNORECASE)
    return len(words) > 1

def is_english(text: str) -> bool:
    try:
        # Require at least 3 characters for reliable detection
        if len(text.strip()) < 3:
            return False
        return detect(text) == 'en'
    except LangDetectException:
        return False
    
def contains_keyword(text: str, keyword: str) -> bool:
    """Check if text contains the keyword"""
    return re.search(rf'\b{re.escape(keyword)}\b', text, re.IGNORECASE) is not None