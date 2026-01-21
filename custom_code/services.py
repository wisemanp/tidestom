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