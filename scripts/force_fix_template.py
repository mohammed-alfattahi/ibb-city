
import os
import time

path = r"c:\Users\Owner\Desktop\ibbb\ibb\templates\place_list.html"

def fix_file():
    try:
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        new_lines = []
        skip_next = False
        fixed_count = 0
        
        for i in range(len(lines)):
            if skip_next:
                skip_next = False
                continue
                
            line = lines[i]
            
            # Fix duplicate multiline tag for category
            if 'request.GET.category|stringformat:"s"==cat.id|stringformat:"s"' in line:
                # Check if it continues on next line
                if i + 1 < len(lines) and '%}' in lines[i+1]:
                     indent = line[:line.find('<')]
                     # Clean fixed line
                     new_line = indent + '<option value="{{ cat.id }}" {% if request.GET.category|stringformat:"s" == cat.id|stringformat:"s" %}selected{% endif %}>\n'
                     new_lines.append(new_line)
                     skip_next = True
                     fixed_count += 1
                     print("Fixed category filter")
                     continue

            # Fix min_rating spacing if needed (though user said I fixed it, let's be sure)
            if 'request.GET.min_rating' in line and '==' in line:
                 # Ensure spaces
                 if '=="' in line:
                     new_line = line.replace('=="', ' == "')
                     new_lines.append(new_line)
                     fixed_count += 1
                     print(f"Fixed rating filter at line {i+1}")
                     continue

            new_lines.append(line)

        if fixed_count > 0:
            with open(path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            print(f"Successfully fixed {fixed_count} issues in place_list.html")
            # Force fsync
            try:
                os.sync()
            except:
                pass
        else:
            print("No issues found to fix.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fix_file()
