import os
import re

def scan_templates():
    template_dir = os.path.join(os.getcwd(), 'templates')
    print(f"Scanning {template_dir} for multi-line Django tags...")
    
    # Regex for {{ ... }} spanning multiple lines
    # We look for {{, then anything including newlines, then }}
    pattern = re.compile(r'\{\{[^}]*?\n[^}]*?\}\}', re.DOTALL)
    
    found = False
    for root, dirs, files in os.walk(template_dir):
        for file in files:
            if file.endswith('.html'):
                path = os.path.join(root, file)
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    matches = pattern.findall(content)
                    for match in matches:
                        # Ignore if it's just comments or valid multiline block tags (this regex matches {{ }})
                        # We specifically want variable tags {{ }} that have newlines
                        print(f"[!] Found multi-line variable tag in {file}:")
                        print(f"    {match.strip()[:50]}...")
                        found = True
                        
    if not found:
        print("No suspicious multi-line variable tags found.")

if __name__ == "__main__":
    scan_templates()
