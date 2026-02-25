import os
import re

def fix_templates():
    template_dir = os.path.join(os.getcwd(), 'templates')
    print(f"Scanning {template_dir} for multi-line Django tags to fix...")
    
    # Regex for {{ ... }} and {% ... %} spanning multiple lines
    # Captures: 1=StartTag, 2=Content, 3=EndTag
    pattern = re.compile(r'(\{\{|{%)(.*?)(\}\}|%\})', re.DOTALL)
    
    fixed_count = 0
    
    for root, dirs, files in os.walk(template_dir):
        for file in files:
            if file.endswith('.html'):
                path = os.path.join(root, file)
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                def replace_match(match):
                    start_tag = match.group(1)
                    inner_content = match.group(2)
                    end_tag = match.group(3)
                    
                    if '\n' in inner_content:
                        # Collapse whitespace: replace newlines and multiple spaces with a single space
                        cleaned_content = re.sub(r'\s+', ' ', inner_content)
                        return f"{start_tag}{cleaned_content}{end_tag}"
                    return match.group(0)

                new_content, count = pattern.subn(replace_match, content)
                
                if count > 0 and new_content != content:
                    print(f"Fixing {count} tags in {file}...")
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    fixed_count += 1
                    
    print(f"Fixed tags in {fixed_count} files.")

if __name__ == "__main__":
    fix_templates()
