from django.db.models import Q
from django.contrib.auth import get_user_model
from .models import TidesTarget, Tag, TargetTag

User = get_user_model()

def get_released_tag():
    return Tag.objects.get(name='released')

def is_released(target: TidesTarget) -> bool:
    rel_tag = get_released_tag()
    return TargetTag.objects.filter(tides=target, tag=rel_tag).exists()

def mark_released(targets, user: User | None = None):
    """Attach the 'released' tag to all given targets."""
    rel_tag = get_released_tag()
    created = 0
    for t in targets:
        _, c = TargetTag.objects.get_or_create(
            tides=t, tag=rel_tag, defaults={'user': user}
        )
        if c:
            created += 1
    return created

def unmark_released(targets):
    """Remove the 'released' tag from all given targets."""
    rel_tag = get_released_tag()
    return TargetTag.objects.filter(tides__in=targets, tag=rel_tag).delete()[0]

def unreleased_queryset():
    """All targets that do NOT have the 'released' tag."""
    rel_tag = get_released_tag()
    # TidesTarget inherits BaseTarget, so join via basetarget
    return (
        TidesTarget.objects
        .exclude(target_tags__tag=rel_tag)  # target_tags is related_name on TargetTag.tides
    )

def queued_by_auto_prob(min_prob: float):
    """
    Targets with auto classification prob >= min_prob that are not released yet.
    Adjust field names if your auto prob field differs.
    """
    qs = unreleased_queryset()
    if hasattr(TidesTarget, 'auto_tidesclass_prob'):
        qs = qs.filter(auto_tidesclass_prob__gte=min_prob)
    return qs

def filter_by_tags(qs, include_tags=None, exclude_tags=None):
    """
    Filter a queryset of TidesTarget by inclusion/exclusion of tags.
    include_tags/exclude_tags: iterables of Tag or tag names.
    """
    include_tags = include_tags or []
    exclude_tags = exclude_tags or []

    if include_tags:
        inc_q = Q()
        for t in include_tags:
            name = t.name if hasattr(t, 'name') else str(t)
            inc_q |= Q(target_tags__tag__name=name)
        qs = qs.filter(inc_q)

    if exclude_tags:
        for t in exclude_tags:
            name = t.name if hasattr(t, 'name') else str(t)
            qs = qs.exclude(target_tags__tag__name=name)

    return qs.distinct()

def released_queryset():
    rel_tag = get_released_tag()
    return TidesTarget.objects.filter(target_tags__tag=rel_tag)


def get_staged_tag():
    """Get or create the 'staged' system tag."""
    tag, _ = Tag.objects.get_or_create(
        name='staged',
        defaults={
            'description': 'Target is in staging area for next release',
            'is_system': True,
            'is_clickable': False,
            'is_active': True,
        }
    )
    return tag


def staged_queryset():
    """All targets that have the 'staged' tag but not 'released'."""
    staged_tag = get_staged_tag()
    released_tag = get_released_tag()
    return (
        TidesTarget.objects
        .filter(target_tags__tag=staged_tag)
        .exclude(target_tags__tag=released_tag)
    )


def update_staging_area():
    """
    Update staging area with new observations since last release.
    Returns count of newly staged targets.
    """
    from .models import TidesSpec
    from django.utils import timezone
    from datetime import timedelta
    
    # Find the most recent release time
    released_tag = get_released_tag()
    last_release = (
        TargetTag.objects
        .filter(tag=released_tag)
        .order_by('-created')
        .values_list('created', flat=True)
        .first()
    )
    
    # If no releases yet, use 24h ago as cutoff
    if not last_release:
        last_release = timezone.now() - timedelta(days=1)
    
    # Find targets with spectra observed after last release
    recent_spectra = TidesSpec.objects.filter(obs_date__gt=last_release)
    tides_ids = recent_spectra.values_list('tides_id', flat=True).distinct()
    
    # Get targets that aren't already released or staged
    staged_tag = get_staged_tag()
    targets_to_stage = (
        TidesTarget.objects
        .filter(pk__in=tides_ids)
        .exclude(target_tags__tag=released_tag)
        .exclude(target_tags__tag=staged_tag)
    )
    
    # Add staged tag to these targets
    count = 0
    for target in targets_to_stage:
        TargetTag.objects.get_or_create(
            tides=target,
            tag=staged_tag,
            defaults={'user': None}
        )
        count += 1
    
    return count


def promote_staged_to_released(user=None):
    """
    Move all staged targets to released.
    Returns count of promoted targets.
    """
    staged_tag = get_staged_tag()
    released_tag = get_released_tag()
    
    staged_targets = staged_queryset()
    count = 0
    
    for target in staged_targets:
        # Add released tag
        TargetTag.objects.get_or_create(
            tides=target,
            tag=released_tag,
            defaults={'user': user}
        )
        # Remove staged tag
        TargetTag.objects.filter(tides=target, tag=staged_tag).delete()
        count += 1
    
    return count