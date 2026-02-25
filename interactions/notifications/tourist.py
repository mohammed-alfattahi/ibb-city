"""
Tourist Notifications
إشعارات السائح
"""
from .base import NotificationBase


class TouristNotifications(NotificationBase):
    """إشعارات خاصة بالسياح"""
    
    @classmethod
    def notify_review_reply(cls, review_reply):
        """إشعار السائح بالرد على تعليقه"""
        return cls._create_notification(
            recipient=review_reply.review.user,
            notification_type='review_reply',
            title='💬 رد على تقييمك',
            message=f'رد {review_reply.replier.full_name or review_reply.replier.username} على تقييمك لـ "{review_reply.review.place.name}".',
            related_object=review_reply,
            action_url=f'/place/{review_reply.review.place.pk}/#reviews'
        )

    @classmethod
    def notify_new_comment(cls, comment):
        """إشعار بتعليق جديد"""
        return cls._create_notification(
            recipient=comment.place.owner,
            notification_type='new_review',
            title='💬 تعليق جديد',
            message=f'وأضاف {comment.user.username} تعليقاً على "{comment.place.name}".',
            related_object=comment,
            action_url=f'/place/{comment.place.pk}/#comments'
        )

    @classmethod
    def notify_comment_reply(cls, comment):
        """إشعار بالرد على تعليق (Threaded)"""
        if not comment.parent:
            return None
            
        return cls._create_notification(
            recipient=comment.parent.user,
            notification_type='review_reply',
            title='💬 رد على تعليقك',
            message=f'رد {comment.user.username} على تعليقك في "{comment.place.name}".',
            related_object=comment,
            action_url=f'/place/{comment.place.pk}/#comments'
        )
    
    @classmethod
    def notify_report_update(cls, report, status_message):
        """إشعار بتحديث حالة البلاغ"""
        notification_type = 'report_resolved' if report.status == 'RESOLVED' else 'report_update'
        title = '✅ تم حل بلاغك' if report.status == 'RESOLVED' else '📝 تحديث على بلاغك'
        
        return cls._create_notification(
            recipient=report.user,
            notification_type=notification_type,
            title=title,
            message=status_message,
            related_object=report,
            action_url=f'/reports/{report.pk}/'
        )
    
    @classmethod
    def notify_favorite_status_change(cls, favorite, is_suspended):
        """إشعار بتغيير حالة منشأة محفوظة"""
        notification_type = 'favorite_suspended' if is_suspended else 'favorite_reactivated'
        title = '⚠️ تم إيقاف منشأة محفوظة' if is_suspended else '✅ تم إعادة تفعيل منشأة محفوظة'
        status_text = "إيقافها مؤقتاً" if is_suspended else "إعادة تفعيلها"
        message = f'المنشأة "{favorite.place.name}" التي حفظتها في المفضلة تم {status_text}.'
        
        return cls._create_notification(
            recipient=favorite.user,
            notification_type=notification_type,
            title=title,
            message=message,
            related_object=favorite.place,
            action_url=f'/place/{favorite.place.pk}/'
        )

    @classmethod
    def notify_favorite_new_offer(cls, ad, favorited_users):
        """إشعار للمستخدمين الذين فضلوا المكان بوجود عرض جديد"""
        notifications = []
        for user in favorited_users:
            notifications.append(cls._create_notification(
                recipient=user,
                notification_type='favorite_new_offer',
                title='🔥 عرض جديد!',
                message=f'منشأتك المفضلة "{ad.place.name}" لديها عرض جديد.',
                related_object=ad,
                action_url=f'/place/{ad.place.pk}/'
            ))
        return notifications
