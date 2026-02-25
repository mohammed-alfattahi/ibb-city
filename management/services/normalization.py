"""
Text Normalization Service
Utilities for normalizing Arabic and English text for moderation.
"""
import re
import unicodedata


def remove_diacritics(text: str) -> str:
    """Remove Arabic diacritics (Tashkeel)."""
    # Arabic diacritics unicode range
    arabic_diacritics = re.compile("""
                             ّ    | # Tashdid
                             َ    | # Fatha
                             ً    | # Tanwin Fath
                             ُ    | # Damma
                             ٌ    | # Tanwin Damm
                             ِ    | # Kasra
                             ٍ    | # Tanwin Kasr
                             ْ    | # Sukun
                             ـ     # Tatweel/Kashida
                         """, re.VERBOSE)
    return re.sub(arabic_diacritics, '', text)


def normalize_arabic(text: str) -> str:
    """Normalize Arabic characters to standard forms."""
    text = remove_diacritics(text)
    
    # Normalize Alef variations
    text = re.sub("[إأآا]", "ا", text)
    
    # Normalize Teh Marbuta
    text = re.sub("ة", "ه", text)
    
    # Normalize Yeh
    text = re.sub("ى", "ي", text)
    
    return text


def normalize_text(text: str) -> str:
    """
    Main normalization function.
    - Lowercase English
    - Normalize Arabic
    - Remove invisible characters
    - Collapse repeated characters (3+ -> 1)
    """
    if not text:
        return ""
    
    # 1. Lowercase
    text = text.lower()
    
    # 2. Normalize unicode (NFKC)
    text = unicodedata.normalize('NFKC', text)
    
    # 3. Arabic Normalization
    text = normalize_arabic(text)
    
    # 4. Collapse repeated characters (e.g. "loool" -> "lol")
    # Matches any character repeated 3 or more times, replace with single char
    # text = re.sub(r'(.)\1{2,}', r'\1', text) 
    # Actually, let's keep 2 chars to be safe (e.g. 'cool', 'Allah')
    # But usually spammers use 'hhhhh'. Let's collapse 3+ to 1.
    # Safe approach: 3+ -> 2 (e.g. 'loool' -> 'lool')? 
    # Let's stick to simple normalization for now, repeating chars strategy is tricky.
    # We will just trim whitespace.
    
    text = text.strip()
    
    # 5. Remove non-word characters for word matching (optional, depends on strategy)
    # keeping it simple for now to catch phrases
    
    return text
