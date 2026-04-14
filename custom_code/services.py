from django.db.models import Q
from django.db import models
from django.contrib.auth import get_user_model
from .models import TidesTarget, Tag, TargetTag

User = get_user_model()

# -----------------------------------------------------------
# Released status — now driven by tides_cand.released boolean
# (writable by Prefect or any direct SQL/ORM call)
# -----------------------------------------------------------

def is_released(target: TidesTarget) -> bool:
    return target.released

def mark_released(targets, user=None):
    """Set released=True on all given targets. Returns count updated."""
    return TidesTarget.objects.filter(pk__in=[t.pk for t in targets]).update(released=True)

def unmark_released(targets):
    """Set released=False on all given targets. Returns count updated."""
    return TidesTarget.objects.filter(pk__in=[t.pk for t in targets]).update(released=False)

def released_queryset():
    """All targets with released=True."""
    return TidesTarget.objects.filter(released=True)

def unreleased_queryset():
    """All targets with released=False."""
    return TidesTarget.objects.filter(released=False)

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


def get_needs_review_tag():
    """Get or create the 'needs-review' system tag."""
    tag, _ = Tag.objects.get_or_create(
        name='needs-review',
        defaults={
            'description': 'Target requires human review before release',
            'is_system': True,
            'is_clickable': False,
            'is_active': True,
        }
    )
    return tag


def get_ready_tag():
    """Get or create the 'ready' system tag."""
    tag, _ = Tag.objects.get_or_create(
        name='ready',
        defaults={
            'description': 'Target has been reviewed and approved for release',
            'is_system': True,
            'is_clickable': False,
            'is_active': True,
        }
    )
    return tag


def staged_queryset():
    """All targets that are pending release (needs-review or ready, but not released)."""
    needs_review_tag = get_needs_review_tag()
    ready_tag = get_ready_tag()
    return (
        TidesTarget.objects
        .filter(
            models.Q(target_tags__tag=needs_review_tag) |
            models.Q(target_tags__tag=ready_tag)
        )
        .filter(released=False)
        .distinct()
    )


def update_staging_area():
    """
    Update staging area with new observations since last release.
    Marks new targets as needs-review.
    Returns count of newly staged targets.
    """
    from .models import TidesSpec
    from django.utils import timezone
    from datetime import timedelta

    # Find targets with spectra observed in the last 24h
    cutoff = timezone.now() - timedelta(days=1)
    recent_spectra = TidesSpec.objects.filter(obs_date__gt=cutoff)
    tides_ids = recent_spectra.values_list('tides_id', flat=True).distinct()

    # Get targets that aren't already released or in review
    needs_review_tag = get_needs_review_tag()
    ready_tag = get_ready_tag()
    targets_to_stage = (
        TidesTarget.objects
        .filter(pk__in=tides_ids, released=False)
        .exclude(target_tags__tag=needs_review_tag)
        .exclude(target_tags__tag=ready_tag)
    )

    # Add needs-review tag to new targets
    count = 0
    for target in targets_to_stage:
        TargetTag.objects.get_or_create(
            tides=target,
            tag=needs_review_tag,
            defaults={'user': None}
        )
        count += 1

    return count

