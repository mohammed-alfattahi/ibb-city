from django.test import TestCase
import os
from scripts.check_architecture import scan_directory

class ArchitectureTest(TestCase):
    def test_architecture_compliance(self):
        """Ensure no forbidden imports exist in the codebase."""
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        errors = scan_directory(base_dir)
        
        if errors:
            self.fail(f"Architecture violations found:\n" + "\n".join(errors))
