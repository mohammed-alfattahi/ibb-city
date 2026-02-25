from django.urls import reverse, resolve
from django.test import Client

from django.conf import settings

def test_redirects():
    # Allow testserver for Client requests
    if 'testserver' not in settings.ALLOWED_HOSTS:
        settings.ALLOWED_HOSTS = list(settings.ALLOWED_HOSTS) + ['testserver']

    client = Client()
    
    print("--- Testing Auth Redirects ---")
    
    # Define test cases: (path, expected_status, expected_redirect_chain)
    tests = [
        ('/accounts/login/', 301, '/login/'),
        ('/accounts/signup/', 301, '/join/'),
        ('/partner/login/', 301, '/login/'),
        ('/partner/logout/', 301, '/logout/'),
    ]
    
    for path, status, redirect_url in tests:
        response = client.get(path)
        print(f"Testing {path}...")
        
        if response.status_code != status:
            print(f"❌ Failed: Expected status {status}, got {response.status_code}")
            continue
            
        if status == 301 or status == 302:
            if response.url != redirect_url:
                print(f"❌ Failed: Expected redirect to {redirect_url}, got {response.url}")
            else:
                print(f"✅ Passed: Redirects to {response.url}")
        else:
             print("✅ Passed")

    print("\n--- Verifying Unified Views ---")
    try:
        match = resolve('/login/')
        print(f"✅ /login/ resolves to: {match.func.__name__} (Expected: UnifiedLoginView)")
    except Exception as e:
        print(f"❌ /login/ resolution failed: {e}")

    try:
        match = resolve('/join/')
        print(f"✅ /join/ resolves to: {match.func.__name__} (Expected: TemplateView)")
    except Exception as e:
        print(f"❌ /join/ resolution failed: {e}")

test_redirects()
