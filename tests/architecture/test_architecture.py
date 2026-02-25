import pytest

def test_architecture():
    """
    Run import-linter within the test suite.
    This ensures that architecture rules are enforced during CI/CD.
    """
    try:
        from importlinter.application import check_contracts_and_print_report, read_configuration
    except ImportError:
        pytest.skip("import-linter not installed. Skipping architecture tests.")

    try:
        # Read default configuration from .importlinter
        # Note: If running from root, it should pick it up automatically if passed to the checker
        # However, check_contracts_and_print_report expects configuration arguments or loads default?
        # It usually runs CLI.
        
        # We can implement a simple check using simple shell command if API is complex, 
        # but let's try to run it via subprocess to simulate CLI behavior which is robust.
        import subprocess
        result = subprocess.run(['lint-imports', '--config', '.importlinter'], capture_output=True, text=True)
        
        if result.returncode != 0:
            pytest.fail(f"Architecture violations found:\n{result.stdout}\n{result.stderr}")
            
    except FileNotFoundError:
        pytest.skip("lint-imports not found. Ensure 'import-linter' is installed.")
