"""
Review Use Cases
حالات استخدام التقييمات
"""
from .base import UseCaseResult


class CreateReviewUseCase:
    """Use case for creating a review with moderation."""
    
    def __init__(self):
        from ibb_guide.domain.policies import ModerationPolicy
        self.moderation = ModerationPolicy()
    
    def execute(self, user, place, rating: int, comment: str) -> UseCaseResult:
        from interactions.services.review_service import ReviewService
        from interactions.notifications import NotificationService
        
        # Step 1: Content moderation
        issues = self.moderation.check_content(comment)
        if issues:
            action = self.moderation.recommend_action(issues, None)
            if action.value in ['delete', 'ban_user']:
                return UseCaseResult(
                    success=False,
                    message=self.moderation.get_warning_message(issues),
                    errors=issues
                )
        
        # Step 2: Create review
        success, result = ReviewService.create_review(user, place, rating, comment)
        
        if not success:
            return UseCaseResult(success=False, message=result)
        
        # Step 3: Notify place owner
        if hasattr(place, 'establishment') and place.establishment.owner:
            NotificationService.notify_user(
                user=place.establishment.owner,
                title='تقييم جديد',
                message=f'{user.username} أضاف تقييماً لـ {place.name}',
                url=f'/place/{place.id}/'
            )
        
        return UseCaseResult(
            success=True,
            message="تم إضافة التقييم بنجاح!",
            data={'review_id': result.id}
        )
