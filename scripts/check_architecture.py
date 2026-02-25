
import os
import ast
import sys

FORBIDDEN_IMPORTS = {
    'domain': ['django.views', 'rest_framework', 'django.forms', 'django.http', 'django.shortcuts'],
    'services': ['django.views', 'rest_framework.views', 'django.forms', 'django.shortcuts'],
}

def check_file(filepath, layer):
    """Check a file for forbidden imports."""
    with open(filepath, 'r', encoding='utf-8') as f:
        try:
            tree = ast.parse(f.read(), filename=filepath)
        except SyntaxError:
            print(f"Syntax error in {filepath}")
            return []

    errors = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                for forbidden in FORBIDDEN_IMPORTS.get(layer, []):
                    if alias.name.startswith(forbidden):
                        errors.append(f"Forbidden import '{alias.name}' in {filepath}:{node.lineno}")
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                for forbidden in FORBIDDEN_IMPORTS.get(layer, []):
                    if node.module.startswith(forbidden):
                        errors.append(f"Forbidden import '{node.module}' in {filepath}:{node.lineno}")

    return errors

def scan_directory(root_path):
    all_errors = []
    print(f"Scanning {root_path} for architecture violations...")
    
    for root, dirs, files in os.walk(root_path):
        for file in files:
            if not file.endswith('.py'):
                continue
            
            filepath = os.path.join(root, file)
            
            # Determine layer
            layer = None
            if 'services' in root:
                layer = 'services'
            elif 'models' in root: # Usually domain logic implies models too, but models rely on django.db
                # layer = 'domain' 
                pass
            
            if layer:
                file_errors = check_file(filepath, layer)
                if file_errors:
                    all_errors.extend(file_errors)
                    
    return all_errors

if __name__ == "__main__":
    project_root = os.getcwd()
    if len(sys.argv) > 1:
        project_root = sys.argv[1]
        
    errors = scan_directory(project_root)
    
    if errors:
        print("\nArchitecture Violations Found:")
        for error in errors:
            print(f"- {error}")
        sys.exit(1)
    else:
        print("\nArchitecture check passed!")
        sys.exit(0)
