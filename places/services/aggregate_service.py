"""Aggregate Service

Handles updating cached aggregates on Establishment.

ملاحظة:
- تم توحيد فلترة التقييمات والتعليقات على visibility_state='visible'
  لضمان أن متوسط التقييم وعدد التقييمات لا يتأثر بالمحتوى المخفي.
"""

import logging
from django.db.models import Avg, Count

logger = logging.getLogger(__name__)


def update_establishment_aggregates(establishment_id: int):
    """Update cached rating/review aggregates for an establishment.

    Call this after rating/review/comment visibility changes.
    """
    from places.models import Establishment
    from interactions.models import Review, PlaceComment

    try:
        establishment = Establishment.objects.get(pk=establishment_id)

        visible_reviews = Review.objects.filter(
            place_id=establishment_id,
            visibility_state='visible'
        )

        rating_stats = visible_reviews.aggregate(
            avg_rating=Avg('rating'),
            rating_count=Count('id')
        )

        # "عدد المراجعات" هنا = عدد التقييمات النصية + عدد التعليقات المرئية
        review_text_count = visible_reviews.exclude(comment='').count()
        comment_count = PlaceComment.objects.filter(
            place_id=establishment_id,
            visibility_state='visible'
        ).count()

        establishment.cached_avg_rating = rating_stats['avg_rating'] or 0
        establishment.cached_rating_count = rating_stats['rating_count'] or 0
        establishment.cached_review_count = review_text_count + comment_count

        establishment.save(update_fields=[
            'cached_avg_rating',
            'cached_rating_count',
            'cached_review_count'
        ])

        logger.info(f"Updated aggregates for establishment {establishment_id}")

    except Exception as e:
        logger.error(f"Failed to update aggregates for {establishment_id}: {e}", exc_info=True)


def recalculate_all_aggregates():
    """Recalculate aggregates for all establishments."""
    from places.models import Establishment

    qs = Establishment.objects.all()
    total = qs.count()
    establishment_ids = qs.values_list('id', flat=True)

    for est_id in establishment_ids:
        update_establishment_aggregates(est_id)

    logger.info(f"Recalculated aggregates for {total} establishments")
