# workspaces/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from guardian.shortcuts import assign_perm
from .models import UserWorkspace

@receiver(post_save, sender=get_user_model())
def create_user_workspace(sender, instance, created, **kwargs):
    if created:
        workspace = UserWorkspace.get_or_create_for_user(instance)
        assign_perm('view_userworkspace', instance, workspace)
        assign_perm('change_userworkspace', instance, workspace)

