"""
Management command to seed UI/CMS data for the admin interfaces.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from management.models import (
    HomePageSection, HeroSlide, Menu, SidebarWidget, SidebarLink,
    SocialLink, SiteSetting, CulturalLandmark, PublicEmergencyContact,
    SafetyGuideline, TeamMember, TransportCompany, ListingConfiguration,
    PlaceDetailBlock
)


class Command(BaseCommand):
    help = 'Seeds the database with UI/CMS sample data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding UI data...')
        
        with transaction.atomic():
            self.create_site_settings()
            self.create_social_links()
            self.create_menus()
            self.create_sidebar_widgets()
            self.create_hero_slides()
            self.create_home_sections()
            self.create_emergency_contacts()
            self.create_safety_guidelines()
            self.create_cultural_landmarks()
            self.create_team_members()
            self.create_transport_companies()
            self.create_listing_configs()
            self.create_place_detail_blocks()

        self.stdout.write(self.style.SUCCESS('Successfully seeded UI data!'))

    def create_site_settings(self):
        self.stdout.write('Creating site settings...')
        SiteSetting.objects.all().delete()
        SiteSetting.objects.create(
            site_name='دليل إب السياحي',
            footer_text='دليلك الشامل للسياحة في محافظة إب اليمنية',
            copyright_text='© 2026 دليل إب السياحي - جميع الحقوق محفوظة',
            contact_email='info@ibbguide.com',
            contact_phone='+967-4-123456',
            address='محافظة إب، اليمن',
            meta_description='دليلك الشامل للسياحة في محافظة إب اليمنية',
            keywords='إب، سياحة، يمن، فنادق'
        )

    def create_social_links(self):
        self.stdout.write('Creating social links...')
        SocialLink.objects.all().delete()
        links = [
            ('فيسبوك', 'https://facebook.com/ibbguide', 'fab fa-facebook'),
            ('تويتر', 'https://twitter.com/ibbguide', 'fab fa-twitter'),
            ('انستغرام', 'https://instagram.com/ibbguide', 'fab fa-instagram'),
        ]
        for i, (label, url, icon) in enumerate(links):
            SocialLink.objects.create(label=label, url=url, icon=icon, order=i)

    def create_menus(self):
        self.stdout.write('Creating menus...')
        Menu.objects.all().delete()
        menus = [
            ('header', 'القائمة الرئيسية', '/'),
            ('header', 'الأماكن', '/places/'),
            ('header', 'الفعاليات', '/events/'),
            ('footer', 'من نحن', '/about/'),
            ('footer', 'اتصل بنا', '/contact/'),
        ]
        for i, (loc, title, url) in enumerate(menus):
            Menu.objects.create(location=loc, title=title, url=url, order=i)

    def create_sidebar_widgets(self):
        self.stdout.write('Creating sidebar widgets...')
        SidebarWidget.objects.all().delete()
        
        widget1 = SidebarWidget.objects.create(
            title='روابط سريعة',
            widget_type='links',
            is_visible=True,
            order=0
        )
        quick_links = [
            ('الصفحة الرئيسية', '/'),
            ('دليل الأماكن', '/places/'),
        ]
        for i, (title, url) in enumerate(quick_links):
            SidebarLink.objects.create(widget=widget1, title=title, url=url, order=i)
        
        SidebarWidget.objects.create(
            title='إحصائيات',
            widget_type='stats',
            content='{"places": 150, "partners": 45}',
            is_visible=True,
            order=1
        )

    def create_hero_slides(self):
        self.stdout.write('Creating hero slides...')
        HeroSlide.objects.all().delete()
        slides = [
            ('اكتشف إب الخضراء', 'وجهتك المثالية للسياحة', 'استكشف الآن', '/places/'),
            ('الطبيعة الخلابة', 'جبال وشلالات ووديان ساحرة', 'شاهد المزيد', '/nature/'),
        ]
        for i, (title, subtitle, btn_text, btn_link) in enumerate(slides):
            HeroSlide.objects.create(
                title=title,
                subtitle=subtitle,
                button_text=btn_text,
                button_link=btn_link,
                is_active=True,
                order=i
            )

    def create_home_sections(self):
        self.stdout.write('Creating home page sections...')
        HomePageSection.objects.all().delete()
        sections = [
            ('hero', 'قسم العرض الرئيسي'),
            ('featured_grid', 'الأماكن المميزة'),
            ('quick_access', 'وصول سريع'),
            ('stats', 'إحصائيات الموقع'),
        ]
        for i, (stype, title) in enumerate(sections):
            HomePageSection.objects.create(
                section_type=stype,
                title=title,
                is_visible=True,
                order=i
            )

    def create_emergency_contacts(self):
        self.stdout.write('Creating emergency contacts...')
        PublicEmergencyContact.objects.all().delete()
        contacts = [
            ('الطوارئ العامة', '199', 'danger', 'fas fa-ambulance'),
            ('الشرطة', '194', 'primary', 'fas fa-shield-alt'),
            ('الإطفاء', '191', 'warning', 'fas fa-fire-extinguisher'),
            ('المستشفى الجمهوري', '04-123456', 'success', 'fas fa-hospital'),
        ]
        for i, (title, number, color, icon) in enumerate(contacts):
            PublicEmergencyContact.objects.create(
                title=title,
                number=number,
                color=color,
                icon=icon,
                is_active=True,
                order=i
            )

    def create_safety_guidelines(self):
        self.stdout.write('Creating safety guidelines...')
        SafetyGuideline.objects.all().delete()
        guidelines = [
            ('احترم العادات المحلية', 'تأكد من احترام التقاليد والعادات اليمنية', 'primary', 'fas fa-hands'),
            ('احمل وثائقك دائماً', 'احتفظ بنسخة من جواز سفرك', 'warning', 'fas fa-id-card'),
            ('اشرب مياه معبأة', 'تجنب شرب مياه الصنبور', 'success', 'fas fa-tint'),
        ]
        for i, (title, desc, color, icon) in enumerate(guidelines):
            SafetyGuideline.objects.create(
                title=title,
                description=desc,
                color=color,
                icon=icon,
                is_active=True,
                order=i
            )

    def create_cultural_landmarks(self):
        self.stdout.write('Creating cultural landmarks...')  
        CulturalLandmark.objects.all().delete()
        landmarks = [
            ('جبل صبر', 'أعلى قمة في محافظة إب', 'fas fa-mountain', 'success'),
            ('قلعة القاهرة', 'قلعة تاريخية تعود للعصر الإسلامي', 'fas fa-fort-awesome', 'warning'),
            ('سوق إب القديم', 'سوق تقليدي يعكس الحياة اليومية', 'fas fa-store', 'primary'),
        ]
        for i, (title, desc, icon, color) in enumerate(landmarks):
            CulturalLandmark.objects.create(
                title=title,
                description=desc,
                icon=icon,
                color=color,
                is_active=True,
                order=i
            )

    def create_team_members(self):
        self.stdout.write('Creating team members...')
        TeamMember.objects.all().delete()
        members = [
            ('أحمد محمد', 'المدير التنفيذي', 'خبرة 10 سنوات في السياحة'),
            ('سارة علي', 'مديرة التسويق', 'متخصصة في التسويق الرقمي'),
        ]
        for i, (name, role, bio) in enumerate(members):
            TeamMember.objects.create(
                name=name,
                role=role,
                bio=bio,
                is_active=True,
                order=i
            )

    def create_transport_companies(self):
        self.stdout.write('Creating transport companies...')
        TransportCompany.objects.all().delete()
        companies = [
            ('باصات النجم', '777123456', 'نقل بين المدن'),
            ('تاكسي إب', '733987654', 'خدمة تاكسي 24 ساعة'),
        ]
        for i, (name, phone, desc) in enumerate(companies):
            TransportCompany.objects.create(
                name=name,
                phone=phone,
                description=desc,
                is_active=True,
                order=i
            )

    def create_listing_configs(self):
        self.stdout.write('Creating listing configurations...')
        ListingConfiguration.objects.all().delete()
        configs = [
            ('place_list', 'دليل الأماكن', 'استكشف أفضل الأماكن في إب'),
        ]
        for page_name, title, subtitle in configs:
            ListingConfiguration.objects.create(
                page_name=page_name,
                hero_title=title,
                hero_subtitle=subtitle
            )

    def create_place_detail_blocks(self):
        self.stdout.write('Creating place detail blocks...')
        PlaceDetailBlock.objects.all().delete()
        blocks = [
            ('hero', 'القسم الرئيسي'),
            ('gallery', 'معرض الصور'),
            ('overview', 'نظرة عامة'),
            ('reviews', 'التقييمات'),
            ('map', 'الموقع على الخريطة'),
        ]
        for i, (block_type, title) in enumerate(blocks):
            PlaceDetailBlock.objects.create(
                block_type=block_type,
                title=title,
                is_visible=True,
                order=i
            )
