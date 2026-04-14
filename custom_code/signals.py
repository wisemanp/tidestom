import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from custom_code.models import TargetTag, TidesSpec

logger = logging.getLogger(__name__)


@receiver(post_save, sender=TargetTag)
def sync_review_status_on_tag_add(sender, instance, created, **kwargs):
    """
    When 'auto classification ok' is added → promote to ready, clear needs-review.
    When 'auto classification bad' is added → force needs-review, clear ready.
    """
    if not created:
        return

    tag_name = instance.tag.name
    if tag_name not in ('auto classification ok', 'auto classification bad'):
        return

    try:
        from custom_code.services import get_needs_review_tag, get_ready_tag
        target = instance.tides
        needs_review_tag = get_needs_review_tag()
        ready_tag = get_ready_tag()

        if tag_name == 'auto classification ok':
            TargetTag.objects.get_or_create(tides=target, tag=ready_tag, defaults={'user': None})
            TargetTag.objects.filter(tides=target, tag=needs_review_tag).delete()
        elif tag_name == 'auto classification bad':
            TargetTag.objects.get_or_create(tides=target, tag=needs_review_tag, defaults={'user': None})
            TargetTag.objects.filter(tides=target, tag=ready_tag).delete()
    except Exception as e:
        logger.error(
            f"Failed to sync review status for target {instance.tides_id} on tag '{tag_name}': {e}"
        )


@receiver(post_save, sender=TidesSpec)
def auto_stage_new_spectrum(sender, instance, created, **kwargs):
    """
    When a new spectrum is created, automatically tag its target as 'needs-review'
    if it's not already released or in the queue.
    """
    if not created:
        return

    try:
        from custom_code.services import get_needs_review_tag, get_ready_tag

        target = instance.tides
        if not target:
            return

        # Check if already released
        if target.released:
            return

        # Check if already in queue (needs-review or ready)
        needs_review_tag = get_needs_review_tag()
        ready_tag = get_ready_tag()
        if target.target_tags.filter(tag__in=[needs_review_tag, ready_tag]).exists():
            return

        # Add needs-review tag
        TargetTag.objects.get_or_create(
            tides=target,
            tag=needs_review_tag,
            defaults={'user': None}
        )
    except Exception as e:
        # Don't let tagging errors break spectrum creation
        logger.error(f"Failed to auto-stage target for spectrum {instance.qmost_id}: {e}")
