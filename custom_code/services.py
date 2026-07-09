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


def promote_staged_to_released():
    """
    Promote all 'ready'-tagged unreleased targets to public.

    For each target:
      - Tags 'auto classification bad' OR 'human classification ok'
        → use the most recent HumanClassification
      - Otherwise → use PipelineClassificationGlobal (auto)

    Writes/updates a PublicClassification snapshot, then sets released=True.
    Returns the number of targets released.
    """
    from .models import PublicClassification, TidesClass, TidesClassSubClass

    ready_tag = get_ready_tag()
    targets = (
        TidesTarget.objects
        .filter(target_tags__tag=ready_tag, released=False)
        .distinct()
    )

    count = 0
    for target in targets:
        tags = set(target.target_tags.values_list('tag__name', flat=True))
        use_human = (
            'auto classification bad' in tags or
            'human classification ok' in tags
        )

        pc_kwargs = {}

        if use_human:
            human = target.latest_human_classification
            if human:
                tidesclass = None
                try:
                    tidesclass = TidesClass.objects.get(name=human.sn_type)
                except Exception:
                    pass
                tidesclass_subclass = None
                if tidesclass and human.sn_subtype:
                    try:
                        tidesclass_subclass = TidesClassSubClass.objects.get(
                            main_class=tidesclass, sub_class=human.sn_subtype
                        )
                    except Exception:
                        pass
                pc_kwargs = {
                    'source': PublicClassification.SOURCE_HUMAN,
                    'sn_type': human.sn_type,
                    'tidesclass': tidesclass,
                    'tidesclass_subclass': tidesclass_subclass,
                    'z': human.sn_z,
                    'zerr': None,
                    'probability': None,
                    'phase': human.phase,
                    'notes': human.comments,
                }
            else:
                use_human = False  # no human class exists; fall back to auto

        if not use_human:
            auto = (
                target.pipeline_classifications_global
                .select_related('tidesclass', 'tidesclass_subclass')
                .order_by('-id')
                .first()
            )
            pc_kwargs = {
                'source': PublicClassification.SOURCE_AUTO,
                'sn_type': (
                    auto.tidesclass.name if auto and auto.tidesclass_id
                    else (auto.sn_type if auto else None)
                ),
                'tidesclass': auto.tidesclass if auto and auto.tidesclass_id else None,
                'tidesclass_subclass': (
                    auto.tidesclass_subclass if auto and auto.tidesclass_subclass_id else None
                ),
                'z': auto.z if auto else None,
                'zerr': auto.zerr if auto else None,
                'probability': auto.probability if auto else None,
                'phase': auto.phase if auto else None,
                'notes': auto.notes if auto else None,
            }

        PublicClassification.objects.update_or_create(
            tides=target,
            defaults=pc_kwargs,
        )
        count += 1

    # Bulk-flip released flag
    TidesTarget.objects.filter(
        target_tags__tag=ready_tag, released=False
    ).distinct().update(released=True)

    return count

