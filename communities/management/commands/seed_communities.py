from django.core.management.base import BaseCommand
from communities.models import Community
from django.utils.text import slugify

class Command(BaseCommand):
    help = 'Seeds initial communities for testing'

    def handle(self, *args, **kwargs):
        communities_data = [
            {
                'name': 'عشاق التصوير',
                'description': 'مجتمع يجمع المصورين المحترفين والهواة في إب لتبادل الخبرات والصور.',
                'slug': 'photography-lovers',
                'is_official': True,
            },
            {
                'name': 'رحالة إب',
                'description': 'مجموعة لمحبي المشي الجبلي واستكشاف المناطق الطبيعية في المحافظة.',
                'slug': 'ib-hikers',
                'is_official': True,
            },
            {
                'name': 'دليل المطاعم',
                'description': 'شاركونا تجاربكم وتقييماتكم لأفضل المطاعم والمقاهي في المدينة.',
                'slug': 'foodies-guide',
                'is_official': False,
            }
        ]

        for data in communities_data:
            community, created = Community.objects.get_or_create(
                slug=data['slug'],
                defaults={
                    'name': data['name'],
                    'description': data['description'],
                    'is_official': data['is_official']
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created community: {community.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Community already exists: {community.name}'))
