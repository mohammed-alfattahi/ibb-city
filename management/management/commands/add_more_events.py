"""
Add more sample events to the database.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = 'Add more sample events'

    def handle(self, *args, **options):
        from events.models import Event, Season
        
        now = timezone.now()
        season = Season.objects.first()
        
        events = [
            {'title': 'ليلة شعرية يمنية', 'description': 'أمسية شعرية تجمع شعراء اليمن لإلقاء قصائدهم في أجواء تراثية أصيلة.', 'event_type': 'cultural', 'location': 'دار الثقافة - إب'},
            {'title': 'ماراثون إب الخيري', 'description': 'سباق جري خيري لدعم الأيتام والمحتاجين في المحافظة.', 'event_type': 'sports', 'location': 'ساحة التحرير'},
            {'title': 'معرض الحرف اليدوية', 'description': 'معرض يعرض أجمل الحرف اليدوية اليمنية من نسيج وفخار ومجوهرات.', 'event_type': 'exhibition', 'location': 'المركز الثقافي'},
            {'title': 'مهرجان العسل اليمني', 'description': 'مهرجان سنوي للاحتفاء بالعسل اليمني الطبيعي وأنواعه المختلفة.', 'event_type': 'festival', 'location': 'سوق إب القديم'},
            {'title': 'رحلة تصوير فوتوغرافي', 'description': 'رحلة منظمة للمصورين لالتقاط أجمل المناظر الطبيعية في إب.', 'event_type': 'tour', 'location': 'جبل صبر'},
            {'title': 'ورشة الطبخ اليمني', 'description': 'ورشة عمل لتعلم أسرار الطبخ اليمني التقليدي والأطباق الشعبية.', 'event_type': 'workshop', 'location': 'فندق السلام'},
            {'title': 'حفل موسيقي تراثي', 'description': 'حفل موسيقي يضم فرقاً تقدم الأغاني اليمنية التراثية الأصيلة.', 'event_type': 'concert', 'location': 'مسرح إب'},
            {'title': 'سوق نهاية الأسبوع', 'description': 'سوق أسبوعي للمنتجات المحلية والعضوية من مزارعي المحافظة.', 'event_type': 'market', 'location': 'ساحة المدينة'},
            {'title': 'جولة الآثار التاريخية', 'description': 'جولة إرشادية لاكتشاف أهم المواقع الأثرية في إب وجبلة.', 'event_type': 'tour', 'location': 'متحف إب'},
            {'title': 'مسابقة الألعاب الشعبية', 'description': 'مسابقات في الألعاب اليمنية التقليدية للأطفال والكبار.', 'event_type': 'sports', 'location': 'متنزه إب الأخضر'},
        ]

        for i, e in enumerate(events):
            start = now + timedelta(days=(i+1)*5)
            event, created = Event.objects.get_or_create(
                title=e['title'],
                defaults={
                    'description': e['description'],
                    'event_type': e.get('event_type', 'other'),
                    'location': e['location'],
                    'start_datetime': start,
                    'end_datetime': start + timedelta(hours=4),
                    'season': season,
                    'is_featured': i < 3,
                }
            )
            if created:
                self.stdout.write(f"Created: {event.title}")
        
        self.stdout.write(self.style.SUCCESS("Done!"))
