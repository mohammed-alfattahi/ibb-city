import os

TARGET_DIR = r"c:\Users\Owner\Desktop\ibbb\ibb\docs\tests"
OLD_URL = "osamaalii.pythonanywhere.com"
NEW_URL = "ibbcity.pythonanywhere.com"

print(f"Scanning {TARGET_DIR}...")
count = 0
for filename in os.listdir(TARGET_DIR):
    if filename.endswith(".md"):
        filepath = os.path.join(TARGET_DIR, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        if OLD_URL in content:
            new_content = content.replace(OLD_URL, NEW_URL)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"Updated: {filename}")
            count += 1
        else:
            print(f"Skipped (no match): {filename}")

print(f"Total files updated: {count}")
