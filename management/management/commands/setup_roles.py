from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from places.models import Place, Establishment
from management.models import Request, Advertisement, ErrorLog
from interactions.models import Review, Report
from users.models import User, PartnerProfile

class Command(BaseCommand):
    help = 'Setup default Roles and Permissions'

    def handle(self, *args, **options):
        # 1. Content Manager
        # Permissions: Manage Places, Establishments, Requests, Ads
        content_manager, created = Group.objects.get_or_create(name='Content Manager')
        
        content_perms = [
            'view_place', 'change_place',
            'view_establishment', 'change_establishment',
            'view_request', 'change_request',
            'view_advertisement', 'change_advertisement',
        ]
        self.assign_permissions(content_manager, content_perms)
        self.stdout.write(self.style.SUCCESS('Content Manager Setup Complete'))

        # 2. Support Agent
        # Permissions: View Users, View Reports, View Reviews
        support_agent, created = Group.objects.get_or_create(name='Support Agent')
        
        support_perms = [
            'view_user',
            'view_partnerprofile',
            'view_review', 'change_review',
            'view_report', 'change_report',
        ]
        self.assign_permissions(support_agent, support_perms)
        self.stdout.write(self.style.SUCCESS('Support Agent Setup Complete'))

        # 3. Site Admin (Super Admin usually, but this is a high-level staff group)
        # All permissions
        site_admin, created = Group.objects.get_or_create(name='Site Admin')
        # Assign all relevant permissions
        all_perms = Permission.objects.filter(content_type__app_label__in=['places', 'users', 'management', 'interactions'])
        site_admin.permissions.set(all_perms)
        self.stdout.write(self.style.SUCCESS('Site Admin Setup Complete'))

    def assign_permissions(self, group, codenames):
        for codename in codenames:
            try:
                perm = Permission.objects.get(codename=codename)
                group.permissions.add(perm)
            except Permission.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Permission not found: {codename}'))
