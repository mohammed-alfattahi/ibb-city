from django.contrib.auth.models import Permission
from django.db.models import Q

class RBACService:
    """
    Role-Based Access Control Service.
    Central Authority for Authorization decisions.
    """

    @staticmethod
    def user_has_permission(user, permission_codename):
        """
        Check if user has a specific permission via their Role or direct Permissions.
        """
        if not user.is_authenticated:
            return False

        if user.is_superuser:
            return True

        # 1. Check Direct Django Permissions
        if user.has_perm(permission_codename):
            return True

        # 2. Check Role Permissions
        if user.role:
            # We assume permission_codename is like 'app.action' or just 'action'
            # Django stores codename as 'add_place', 'change_place', etc.
            # We look for codename match in the Role's permissions
            
            # Split if app_label is provided (e.g., 'places.add_place')
            if '.' in permission_codename:
                app_label, codename = permission_codename.split('.', 1)
                return user.role.permissions.filter(
                    content_type__app_label=app_label,
                    codename=codename
                ).exists()
            else:
                return user.role.permissions.filter(codename=permission_codename).exists()
        
        return False

    @staticmethod
    def user_has_role(user, role_names):
        """
        Check if user has one of the specified roles.
        role_names: str or list of strings
        """
        if not user.is_authenticated or not user.role:
            return False
            
        if isinstance(role_names, str):
            role_names = [role_names]
            
        return user.role.name in role_names
