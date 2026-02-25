import os
import sys
import django
from django.conf import settings
from django.urls import reverse, exceptions

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ibb_guide.settings')
django.setup()

import re

def check_file_content_forbidden(file_path, forbidden_terms):
    print(f"Checking {file_path} for forbidden terms: {forbidden_terms}...")
    if not os.path.exists(file_path):
        print(f"FAIL: File not found: {file_path}")
        return False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    failed = False
    for term in forbidden_terms:
        # Escape the term for regex, then add word boundaries
        # Note: term usually contains dot, so we escape it.
        pattern = r"\b" + re.escape(term) + r"\b"
        if re.search(pattern, content):
            print(f"  FAIL: Found forbidden term '{term}'")
            failed = True
            
    if not failed:
        print("  PASS")
        return True
    return False

def check_file_exists(file_path):
    exists = os.path.exists(file_path)
    status = "PASS" if exists else "FAIL"
    print(f"Checking file exists: {file_path} -> {status}")
    return exists

def check_file_content_required(file_path, required_term):
    print(f"Checking {file_path} for required term: '{required_term}'...")
    if not os.path.exists(file_path):
        print(f"FAIL: File not found: {file_path}")
        return False
        
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    if required_term in content:
        print("  PASS")
        return True
    else:
        print(f"  FAIL: Term '{required_term}' not found")
        return False

def check_url_name(url_name):
    try:
        reverse(url_name)
        print(f"Checking URL name '{url_name}' -> PASS")
        return True
    except exceptions.NoReverseMatch:
        print(f"Checking URL name '{url_name}' -> FAIL (NoReverseMatch)")
        return False
    except Exception as e:
        # Some URLs usually require args, so ReverseMatch is expected if we don't provide them.
        # But verify_tourist_requirements usually implies just checking if the name exists in registry.
        # A simple reverse without args failing might mean it needs args, but it IS registered.
        # Better check:
        # We can iterate over URL resolver, but reverse is standard.
        # If it says "with no arguments not found", the name EXISTS.
        # If it says "is not a registered namespace", it doesn't.
        if "not a valid view function or pattern name" in str(e):
             print(f"Checking URL name '{url_name}' -> FAIL")
             return False
        else:
             # If it fails due to missing args, the name exists!
             print(f"Checking URL name '{url_name}' -> PASS (Found, but needs args)")
             return True

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # Assuming script is in root or scripts/ folder, adjust relative paths
    # If run from root via python scripts/verify..., base_dir is root.
    # Let's assume we run from root.
    
    print("=== Verification Report ===\n")
    
    # 1. Check place_detail.html
    check_file_content_forbidden(
        'templates/place_detail.html',
        ['place.images', 'place.average_rating', 'place.address'] # place.address might be valid if it exists, but user said verify it does NOT contain it (use separate fields?)
    )
    
    # 2. Check files exist
    check_file_exists('templates/places/nearby_results.html')
    check_file_exists('static/js/core/places_interactions.js')
    
    # 3. Check base_core.html
    check_file_content_required('templates/base_core.html', 'places_interactions.js')
    
    # 4. Check URL names
    check_url_name('trigger_sos')
    check_url_name('entry_visa')
    
    print("\n=== End Report ===")

if __name__ == '__main__':
    main()
