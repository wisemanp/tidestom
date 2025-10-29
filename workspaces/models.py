from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from guardian.shortcuts import assign_perm
import hashlib
import os
import logging

logger = logging.getLogger(__name__)

def hash_user_dir(user_id: int):
    salt = getattr(settings, "USER_HASH_SALT", "fallback_salt")
    return hashlib.sha256(f"{user_id}{salt}".encode()).hexdigest()

class UserWorkspace(models.Model):
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE)
    directory = models.CharField(max_length=64, unique=True)

    class Meta:
        verbose_name = "User Workspace"
        verbose_name_plural = "User Workspaces"

    @property
    def path(self):
        return os.path.join(settings.USER_OUTPUT_BASE, self.directory)

    @classmethod
    def get_or_create_for_user(cls, user):
        obj, created = cls.objects.get_or_create(
            user=user,
            defaults={'directory': hash_user_dir(user.id)}
        )

        if created:
            try:
                os.makedirs(obj.path, exist_ok=True)

                assign_perm('view_userworkspace', user, obj)
                assign_perm('change_userworkspace', user, obj)
            except Exception as e:
                logger.error(f"Failed to create workspace directory {obj.path}: {e}")

        return obj
