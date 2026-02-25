"""
Admin Notifications
إشعارات مكتب السياحة (الإدارة)
"""
from django.contrib.auth import get_user_model
from .base import NotificationBase

User = get_user_model()


class AdminNotifications(NotificationBase):
    """إشعارات خاصة بمكتب السياحة والإدارة"""
    
    @classmethod
    def _get_staff_users(cls):
        """الحصول على قائمة الموظفين"""
        return User.objects.filter(is_staff=True)
    
    @classmethod
    def notify_new_partner_registration(cls, partner_profile):
        """إشعار لمكتب السياحة بتسجيل شريك جديد"""
        staff_users = cls._get_staff_users()
        notifications = []
        
        for staff in staff_users:
            notifications.append(cls._create_notification(
                recipient=staff,
                notification_type='new_partner_registration',
                title='تسجيل شريك جديد',
                message=f'تقدم {partner_profile.user.full_name or partner_profile.user.username} بطلب شراكة جديد.',
                related_object=partner_profile,
                action_url=f'/admin/users/partnerprofile/{partner_profile.pk}/change/'
            ))
        
        return notifications

    @classmethod
    def notify_partner_upgrade_request(cls, request_obj):
        """إشعار لمكتب السياحة بطلب ترقية سائح لشريك"""
        staff_users = cls._get_staff_users()
        for staff in staff_users:
            cls._create_notification(
                recipient=staff,
                notification_type='partner_upgrade_request',
                title='طلب ترقية حساب',
                message=f'طلب المستخدم {request_obj.user.username} ترقية حسابه إلى شريك.',
                related_object=request_obj,
                action_url='/admin/management/request/'
            )

    @classmethod
    def notify_establishment_update_request(cls, establishment):
        """إشعار لمكتب السياحة بوجود تحديثات معلقة (تتطلب موافقة)"""
        staff_users = cls._get_staff_users()
        for staff in staff_users:
            cls._create_notification(
                recipient=staff,
                notification_type='establishment_update_request',
                title='طلب تحديث بيانات',
                message=f'تحديثات حساسة بانتظار المراجعة لمنشأة "{establishment.name}".',
                related_object=establishment,
                action_url=f'/admin/management/establishment/{establishment.pk}/change/'
            )

    @classmethod
    def notify_establishment_info_update(cls, establishment, update_type, details=""):
        """إشعار لمكتب السياحة بتحديثات فورية (للعلم فقط)"""
        staff_users = cls._get_staff_users()
        
        titles = {
            'unit': 'تحديث الوحدات',
            'media': 'تحديث الوسائط',
            'info': 'تحديث معلومات'
        }
        title = titles.get(update_type, 'تحديث منشأة')
        
        for staff in staff_users:
            cls._create_notification(
                recipient=staff,
                notification_type='establishment_info_update',
                title=title,
                message=f'تم تحديث {title} لمنشأة "{establishment.name}". {details}',
                related_object=establishment,
                action_url=f'/admin/places/establishment/{establishment.pk}/change/'
            )

    @classmethod
    def notify_new_ad_request(cls, ad):
        """إشعار لمكتب السياحة بطلب إعلان جديد"""
        staff_users = cls._get_staff_users()
        place_name = ad.place.name if ad.place else ad.title
        for staff in staff_users:
            cls._create_notification(
                recipient=staff,
                notification_type='new_ad_request',
                title='طلب إعلان جديد',
                message=f'طلب إعلان جديد من {ad.owner.username} لـ "{place_name}".',
                related_object=ad,
                action_url='/admin/management/advertisement/'
            )

    @classmethod
    def notify_ad_payment_uploaded(cls, ad):
        """إشعار لمكتب السياحة برفع سند الدفع"""
        staff_users = cls._get_staff_users()
        place_name = ad.place.name if ad.place else ad.title
        for staff in staff_users:
            cls._create_notification(
                recipient=staff,
                notification_type='ad_payment_uploaded',
                title='تم رفع سند دفع',
                message=f'قام {ad.owner.username} برفع سند الدفع لإعلان "{place_name}".',
                related_object=ad,
                action_url=f'/admin/management/advertisement/'
            )
    
    @classmethod
    def notify_review_objection(cls, report):
        """إشعار باعتراض على مراجعة (بلاغ)"""
        staff_users = cls._get_staff_users()
        for staff in staff_users:
            cls._create_notification(
                recipient=staff,
                notification_type='review_objection',
                title='اعتراض على مراجعة',
                message=f'اعتراض مقدم من {report.user.username} بخصوص مراجعة.',
                related_object=report,
                action_url=f'/admin/interactions/report/{report.pk}/'
            )
    
    @classmethod
    def notify_new_establishment_request(cls, establishment):
        """إشعار لمكتب السياحة بطلب منشأة جديدة"""
        staff_users = cls._get_staff_users()
        notifications = []
        
        for staff in staff_users:
            notifications.append(cls._create_notification(
                recipient=staff,
                notification_type='new_establishment_request',
                title='طلب منشأة جديدة',
                message=f'تقدم الشريك {establishment.owner.full_name} بطلب إضافة منشأة "{establishment.name}".',
                related_object=establishment,
                action_url=f'/admin/places/establishment/{establishment.pk}/change/'
            ))
        
        return notifications
    
    @classmethod
    def notify_new_user_report(cls, report):
        """إشعار لمكتب السياحة ببلاغ جديد"""
        staff_users = cls._get_staff_users()
        notifications = []
        
        # Determine Place Name safely
        place_name = "Unknown"
        if report.content_object:
            if hasattr(report.content_object, 'place'):
                place_name = report.content_object.place.name
            elif hasattr(report.content_object, 'name'):
                place_name = report.content_object.name
        
        for staff in staff_users:
            notifications.append(cls._create_notification(
                recipient=staff,
                notification_type='new_user_report',
                title='بلاغ جديد',
                message=f'تلقيت بلاغاً جديداً من {report.user.username} بخصوص "{place_name}".',
                related_object=report,
                action_url=f'/admin/interactions/report/{report.pk}/change/'
            ))
        
        return notifications

    @classmethod
    def notify_establishment_contact_updated(cls, establishment, actor, action, contact=None):
        """إشعار لمكتب السياحة بتحديث جهات اتصال المنشأة"""
        staff_users = cls._get_staff_users()
        
        action_map = {
            'added': 'إضافة',
            'updated': 'تحديث',
            'deleted': 'حذف',
            'reordered': 'إعادة ترتيب'
        }
        action_text = action_map.get(action, action)
        
        message = f'قام {actor.first_name or actor.username} بـ {action_text} جهات اتصال "{establishment.name}".'
        if contact and action == 'added':
             message = f'قام {actor.first_name or actor.username} بإضافة جهة اتصال ({contact.get_type_display()}) لـ "{establishment.name}".'

        for staff in staff_users:
            cls._create_notification(
                recipient=staff,
                notification_type='contact_update',
                title='تحديث جهات الاتصال',
                message=message,
                related_object=establishment,
                action_url=f'/admin/places/establishment/{establishment.pk}/change/' # Using standard admin link for now
            )

