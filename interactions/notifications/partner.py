"""
Partner Notifications
إشعارات الشريك التجاري (Partner)
"""
from .base import NotificationBase


class PartnerNotifications(NotificationBase):
    """إشعارات خاصة بالشركاء التجاريين"""
    
    # ==========================================
    # إشعارات طلب الشراكة
    # ==========================================
    
    @classmethod
    def notify_partner_approved(cls, partner_profile):
        """إشعار بقبول طلب الشراكة"""
        return cls._create_notification(
            recipient=partner_profile.user,
            notification_type='partner_approved',
            title='🎉 تم اعتماد حسابك كشريك!',
            message=f'مبروك! تم قبول طلب الشراكة الخاص بك. يمكنك الآن الوصول إلى لوحة التحكم وإضافة منشآتك.',
            related_object=partner_profile,
            action_url='/partner/'
        )
    
    @classmethod
    def notify_partner_rejected(cls, partner_profile, reason=''):
        """إشعار برفض طلب الشراكة"""
        message = f'نأسف لإبلاغك بأنه تم رفض طلب الشراكة.'
        if reason:
            message += f'\n\nالسبب: {reason}'
        
        return cls._create_notification(
            recipient=partner_profile.user,
            notification_type='partner_rejected',
            title='❌ تم رفض طلب الشراكة',
            message=message,
            related_object=partner_profile
        )
    
    @classmethod
    def notify_partner_needs_info(cls, partner_profile, info_message):
        """إشعار بطلب معلومات إضافية"""
        return cls._create_notification(
            recipient=partner_profile.user,
            notification_type='partner_needs_info',
            title='📋 مطلوب معلومات إضافية',
            message=f'يرجى تقديم المعلومات التالية لاستكمال طلب الشراكة:\n\n{info_message}',
            related_object=partner_profile,
            action_url='/partner/profile/'
        )

    @classmethod
    def notify_partner_request_received(cls, partner_profile):
        """إشعار للشريك باستلام طلب اعتماده"""
        return cls._create_notification(
            recipient=partner_profile.user,
            notification_type='general',
            title='تم استلام طلب الشراكة',
            message='تم استلام طلبك للانضمام كشريك تجاري وهو الآن قيد المراجعة.',
            related_object=partner_profile,
            action_url='/partner/profile/'
        )

    # ==========================================
    # إشعارات المنشآت
    # ==========================================
    
    @classmethod
    def notify_establishment_approved(cls, establishment):
        """إشعار بقبول المنشأة"""
        return cls._create_notification(
            recipient=establishment.owner,
            notification_type='establishment_approved',
            title='✅ تم قبول المنشأة',
            message=f'تم قبول منشأة "{establishment.name}" ونشرها على المنصة.',
            related_object=establishment,
            action_url=f'/partner/place/{establishment.pk}/'
        )
    
    @classmethod
    def notify_establishment_rejected(cls, establishment, reason=''):
        """إشعار برفض المنشأة"""
        message = f'تم رفض منشأة "{establishment.name}".'
        if reason:
            message += f'\n\nالسبب: {reason}'
        
        return cls._create_notification(
            recipient=establishment.owner,
            notification_type='establishment_rejected',
            title='❌ تم رفض المنشأة',
            message=message,
            related_object=establishment
        )
    
    @classmethod
    def notify_establishment_suspended(cls, establishment, reason=''):
        """إشعار بإيقاف المنشأة"""
        message = f'تم إيقاف منشأة "{establishment.name}" مؤقتاً.'
        if reason:
            message += f'\n\nالسبب: {reason}'
        
        return cls._create_notification(
            recipient=establishment.owner,
            notification_type='establishment_suspended',
            title='⚠️ تم إيقاف المنشأة',
            message=message,
            related_object=establishment,
            action_url=f'/partner/place/{establishment.pk}/'
        )
    
    @classmethod
    def notify_establishment_reactivated(cls, establishment):
        """إشعار بإعادة تفعيل المنشأة"""
        return cls._create_notification(
            recipient=establishment.owner,
            notification_type='establishment_reactivated',
            title='✅ تم إعادة تفعيل المنشأة',
            message=f'تم إعادة تفعيل منشأة "{establishment.name}" وهي الآن متاحة للجمهور.',
            related_object=establishment,
            action_url=f'/partner/place/{establishment.pk}/'
        )

    @classmethod
    def notify_establishment_submitted(cls, establishment):
        """إشعار عند إرسال المنشأة للمراجعة"""
        return cls._create_notification(
            recipient=establishment.owner,
            notification_type='general', # Use general type for now or add specific
            title='تم استلام طلب إضافة المنشأة',
            message=f'تم استلام طلب إضافة "{establishment.name}" وهو الآن قيد المراجعة.',
            related_object=establishment,
            action_url=f'/partner/place/{establishment.pk}/'
        )
    
    @classmethod
    def notify_establishment_unsuspended(cls, establishment):
        """إشعار بإلغاء إيقاف المنشأة (Package 2 fix)"""
        return cls.notify_establishment_reactivated(establishment)
    
    @classmethod
    def notify_establishment_status_changed(cls, establishment):
        """إشعار بتغيير حالة المنشأة (مفتوح/مغلق) (Package 2 fix)"""
        status_text = "مفتوح" if establishment.is_open_status else "مغلق"
        return cls._create_notification(
            recipient=establishment.owner,
            notification_type='establishment_status_changed',
            title=f'📍 تم تغيير حالة المنشأة',
            message=f'منشأة "{establishment.name}" الآن {status_text}.',
            related_object=establishment,
            action_url=f'/partner/place/{establishment.pk}/'
        )

    @classmethod
    def notify_establishment_request_received(cls, establishment):
        """إشعار للشريك باستلام طلب إضافة منشأة"""
        return cls._create_notification(
            recipient=establishment.owner,
            notification_type='general',
            title='تم استلام طلب المنشأة',
            message=f'تم استلام طلب إضافة "{establishment.name}" وهو قيد المراجعة.',
            related_object=establishment,
            action_url=f'/partner/place/{establishment.pk}/'
        )
    
    @classmethod
    def notify_establishment_update_request_received(cls, establishment):
        """إشعار للشريك باستلام طلب التحديث"""
        return cls._create_notification(
            recipient=establishment.owner,
            notification_type='general',
            title='تم استلام طلب التحديث',
            message=f'جاري مراجعة التحديثات المطلوبة لمنشأة "{establishment.name}".',
            related_object=establishment,
            action_url=f'/partner/place/{establishment.pk}/edit/'
        )

    @classmethod
    def notify_new_review(cls, review):
        """إشعار بتعليق جديد على المنشأة"""
        return cls._create_notification(
            recipient=review.place.owner,
            notification_type='new_review',
            title='💬 تعليق جديد على منشأتك',
            message=f'تلقيت تعليقاً جديداً من {review.user.full_name or review.user.username} على "{review.place.name}" بتقييم {review.rating}/5.',
            related_object=review,
            action_url=f'/place/{review.place.pk}/#reviews'
        )

    # ==========================================
    # إشعارات الإعلانات
    # ==========================================

    @classmethod
    def notify_ad_approved(cls, ad):
        place_name = ad.place.name if ad.place else ad.title
        return cls._create_notification(
            recipient=ad.owner,
            notification_type='ad_approved',
            title='✅ تم قبول الإعلان',
            message=f'تمت الموافقة على إعلانك "{place_name}" وهو الآن نشط.',
            related_object=ad,
            action_url='/partner/ads/'
        )

    @classmethod
    def notify_ad_rejected(cls, ad):
        return cls._create_notification(
            recipient=ad.owner,
            notification_type='ad_rejected',
            title='❌ تم رفض الإعلان',
            message='نأسف، تم رفض طلب الإعلان الخاص بك.',
            related_object=ad,
            action_url='/partner/ads/'
        )

    @classmethod
    def notify_ad_payment_needed(cls, ad):
        place_name = ad.place.name if ad.place else ad.title
        return cls._create_notification(
            recipient=ad.owner,
            notification_type='ad_payment_needed',
            title='💰 مطلوب سند الدفع',
            message=f'يرجى رفع سند الدفع لتفعيل إعلان "{place_name}".',
            related_object=ad,
            action_url=f'/partner/ads/{ad.pk}/pay/'
        )

    @classmethod
    def notify_ad_expiring(cls, ad, days_left):
        place_name = ad.place.name if ad.place else ad.title
        return cls._create_notification(
            recipient=ad.owner,
            notification_type='ad_expiring_soon',
            title='⏳ الإعلان قارب على الانتهاء',
            message=f'إعلانك "{place_name}" سينتهي خلال {days_left} أيام.',
            related_object=ad,
            action_url='/partner/ads/'
        )

    @classmethod
    def notify_ad_expired(cls, ad):
        place_name = ad.place.name if ad.place else ad.title
        return cls._create_notification(
            recipient=ad.owner,
            notification_type='ad_expired',
            title='⏹️ انتهى الإعلان',
            message=f'انتهت فترة إعلانك "{place_name}".',
            related_object=ad,
            action_url='/partner/ads/'
        )

    @classmethod
    def notify_ad_payment_issue(cls, ad, notes=''):
        return cls._create_notification(
            recipient=ad.owner,
            notification_type='ad_payment_issue',
            title='⚠️ مشكلة في سند الدفع',
            message=f'يرجى إعادة رفع سند الدفع للإعلان. ملاحظات الإدارة: {notes}',
            related_object=ad,
            action_url=f'/partner/ads/{ad.pk}/pay/'
        )
