from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
from django.core.cache import cache
from django.db import transaction

from cms.models import UIZone, UIComponent, ZoneComponent, UIRevision


CACHE_VERSION_KEY = "cms:version"


def _get_version() -> int:
    v = cache.get(CACHE_VERSION_KEY)
    if not v:
        v = 1
        cache.set(CACHE_VERSION_KEY, v, None)
    return int(v)


def bump_version() -> None:
    """Invalidate all CMS zone caches by bumping a global cache version."""
    try:
        cache.incr(CACHE_VERSION_KEY)
    except Exception:
        # LocMemCache may not support incr consistently in all setups
        cache.set(CACHE_VERSION_KEY, _get_version() + 1, None)


def zone_cache_key(zone_slug: str, stage: str) -> str:
    return f"cms:zone:{zone_slug}:{stage}:v{_get_version()}"


def get_zone_items(zone_slug: str, stage: str = "published") -> List[ZoneComponent]:
    """Fetch zone items with caching."""
    key = zone_cache_key(zone_slug, stage)
    items = cache.get(key)
    if items is not None:
        return items

    try:
        zone = UIZone.objects.get(slug=zone_slug)
    except UIZone.DoesNotExist:
        cache.set(key, [], 300)
        return []

    qs = (
        zone.components.select_related("component")
        .filter(is_visible=True, stage=stage)
        .order_by("order")
    )
    items = list(qs)
    cache.set(key, items, 600)
    return items


def snapshot_zone(zone: UIZone, stage: str) -> Dict[str, Any]:
    comps = (
        zone.components.select_related("component")
        .filter(stage=stage)
        .order_by("order")
    )
    return {
        "zone": {"slug": zone.slug, "name": zone.name},
        "stage": stage,
        "components": [
            {
                "component_slug": zc.component.slug,
                "component_template": zc.component.template_path,
                "order": zc.order,
                "is_visible": zc.is_visible,
                "data_override": zc.data_override or {},
            }
            for zc in comps
        ],
    }


@transaction.atomic
def copy_zone_components(zone: UIZone, from_stage: str, to_stage: str, user=None, action: str = "copy") -> None:
    """Replace all components in to_stage with those from from_stage."""
    source = list(
        zone.components.filter(stage=from_stage).select_related("component").order_by("order")
    )
    # delete destination stage
    zone.components.filter(stage=to_stage).delete()

    for item in source:
        ZoneComponent.objects.create(
            zone=zone,
            component=item.component,
            order=item.order,
            is_visible=item.is_visible,
            stage=to_stage,
            data_override=item.data_override or {},
        )

    UIRevision.objects.create(
        zone=zone,
        action=action,
        from_stage=from_stage,
        to_stage=to_stage,
        snapshot=snapshot_zone(zone, to_stage),
        created_by=user if getattr(user, "is_authenticated", False) else None,
    )

    bump_version()


@transaction.atomic
def publish_zone(zone: UIZone, user=None) -> None:
    """Publish zone draft -> published."""
    copy_zone_components(zone, "draft", "published", user=user, action="publish")


@transaction.atomic
def revert_to_revision(revision: UIRevision, user=None) -> Tuple[bool, str]:
    """
    Revert a zone to a previous revision state.
    
    Args:
        revision: The UIRevision to revert to
        user: The user performing the revert
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    zone = revision.zone
    snapshot = revision.snapshot
    
    if not snapshot or 'components' not in snapshot:
        return False, "هذه النسخة لا تحتوي على بيانات كافية للاستعادة."
    
    target_stage = snapshot.get('stage', 'published')
    
    # Delete current components in target stage
    zone.components.filter(stage=target_stage).delete()
    
    # Restore components from snapshot
    restored_count = 0
    for comp_data in snapshot['components']:
        try:
            component = UIComponent.objects.get(slug=comp_data['component_slug'])
            ZoneComponent.objects.create(
                zone=zone,
                component=component,
                order=comp_data.get('order', 0),
                is_visible=comp_data.get('is_visible', True),
                stage=target_stage,
                data_override=comp_data.get('data_override', {}),
            )
            restored_count += 1
        except UIComponent.DoesNotExist:
            # Skip if component no longer exists
            continue
    
    # Create revert revision
    UIRevision.objects.create(
        zone=zone,
        action='revert',
        from_stage=f'revision_{revision.pk}',
        to_stage=target_stage,
        snapshot=snapshot_zone(zone, target_stage),
        created_by=user if getattr(user, "is_authenticated", False) else None,
    )
    
    bump_version()
    
    return True, f"تم استعادة {restored_count} مكون بنجاح."


def get_zone_revisions(zone: UIZone, limit: int = 10) -> List[UIRevision]:
    """
    Get recent revisions for a zone.
    
    Args:
        zone: The UIZone to get revisions for
        limit: Maximum number of revisions to return
        
    Returns:
        List of UIRevision objects
    """
    return list(zone.revisions.order_by('-created_at')[:limit])


def compare_revisions(rev1: UIRevision, rev2: UIRevision) -> Dict[str, Any]:
    """
    Compare two revisions and return differences.
    
    Args:
        rev1: First revision
        rev2: Second revision
        
    Returns:
        Dict containing comparison results
    """
    snap1 = rev1.snapshot or {}
    snap2 = rev2.snapshot or {}
    
    comps1 = {c['component_slug']: c for c in snap1.get('components', [])}
    comps2 = {c['component_slug']: c for c in snap2.get('components', [])}
    
    added = set(comps2.keys()) - set(comps1.keys())
    removed = set(comps1.keys()) - set(comps2.keys())
    common = set(comps1.keys()) & set(comps2.keys())
    
    modified = []
    for slug in common:
        if comps1[slug] != comps2[slug]:
            modified.append({
                'slug': slug,
                'before': comps1[slug],
                'after': comps2[slug]
            })
    
    return {
        'added': list(added),
        'removed': list(removed),
        'modified': modified,
        'rev1_date': rev1.created_at,
        'rev2_date': rev2.created_at,
    }

