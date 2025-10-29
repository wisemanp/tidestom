from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from guardian.shortcuts import assign_perm
from django.conf import settings
from .models import UserWorkspace
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=get_user_model())
def create_user_workspace(sender, instance, created, **kwargs):
    if created:
        for api_name in settings.USER_OUTPUT_BASES.keys():
            try:
                workspace_obj, _ = UserWorkspace.get_or_create_for_user(instance, api_name=api_name)

                # assign permissions
                assign_perm('view_userworkspace', instance, workspace_obj)
                assign_perm('change_userworkspace', instance, workspace_obj)
            except Exception as e:
                logger.error(f"Failed to create workspace for user {instance.id} API {api_name}: {e}")
