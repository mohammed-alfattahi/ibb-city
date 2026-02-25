from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.contrib.auth.models import Group
from .models import User

@receiver(post_save, sender=User)
def sync_user_role_to_group(sender, instance, created, **kwargs):
    """
    Syncs the User's custom 'role' field to Django's Group system.
    If a user has a role, they are added to a Group with the same name.
    """
    if instance.role:
        group_name = instance.role.name
        group, _ = Group.objects.get_or_create(name=group_name)
        
        # Ensure user is in this group
        if not instance.groups.filter(name=group_name).exists():
            instance.groups.add(group)
            
        # Optional: Remove from other role-based groups if we enforce single-role
        # for g in instance.groups.all():
        #     if g.name != group_name and Role.objects.filter(name=g.name).exists():
        #         instance.groups.remove(g)
