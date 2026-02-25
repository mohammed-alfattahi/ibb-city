import csv
import io
from users.models import User
from places.models import Place, Category
from django.utils.text import slugify

class CsvImporter:
    """
    Service to handle CSV imports for key models.
    """

    @staticmethod
    def import_users(csv_file):
        """
        Import users from a CSV file.
        Expected format: username, email, password, full_name, phone_number
        """
        decoded_file = csv_file.read().decode('utf-8-sig').splitlines()
        reader = csv.DictReader(decoded_file)
        
        results = {
            'created': 0,
            'errors': []
        }

        for row in reader:
            try:
                username = row.get('username')
                email = row.get('email')
                password = row.get('password')
                
                if not username or not email:
                    continue
                    
                if User.objects.filter(username=username).exists():
                    results['errors'].append(f"User {username} already exists")
                    continue
                    
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password if password else 'DefaultPass123!',
                    full_name=row.get('full_name', ''),
                    phone_number=row.get('phone_number', '')
                )
                results['created'] += 1
                
            except Exception as e:
                results['errors'].append(f"Error importing {row.get('username')}: {str(e)}")
                
        return results

    @staticmethod
    def import_places(csv_file, owner_username):
        """
        Import places from a CSV file.
        Expected format: name, category_name, location
        """
        decoded_file = csv_file.read().decode('utf-8-sig').splitlines()
        reader = csv.DictReader(decoded_file)
        
        try:
            owner = User.objects.get(username=owner_username)
        except User.DoesNotExist:
            return {'created': 0, 'errors': [f"Owner {owner_username} not found"]}
            
        results = {
            'created': 0,
            'errors': []
        }

        for row in reader:
            try:
                name = row.get('name')
                category_name = row.get('category')
                
                if not name:
                    continue
                    
                # Find or create category
                category = None
                if category_name:
                    category, _ = Category.objects.get_or_create(name=category_name)
                    
                place = Place.objects.create(
                    name=name,
                    owner=owner,
                    category=category,
                    description=row.get('description', ''),
                    location_text=row.get('location', '')
                )
                results['created'] += 1
                
            except Exception as e:
                results['errors'].append(f"Error importing {row.get('name')}: {str(e)}")
                
        return results
