from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from guardian.shortcuts import assign_perm
import hashlib
import os
import logging
import pwd
import grp

logger = logging.getLogger(__name__)

def hash_user_dir(user_id: int):
    salt = getattr(settings, "USER_HASH_SALT", "fallback_salt")
    return hashlib.sha256(f"{user_id}{salt}".encode()).hexdigest()

def ensure_dir(path: str, owner_user="sniduser", owner_group="snidgroup", mode=0o770):
    """Create a directory and set ownership and permissions."""
    os.makedirs(path, exist_ok=True)
    try:
        uid = pwd.getpwnam(owner_user).pw_uid
        gid = grp.getgrnam(owner_group).gr_gid
        os.chown(path, uid, gid)
        os.chmod(path, mode)
    except KeyError:
        logger.warning(f"User or group not found: {owner_user}:{owner_group}. \
                Skipping chown.")

class UserWorkspace(models.Model):
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE)
    api_name  = models.CharField(max_length=50)
    directory = models.CharField(max_length=64, unique=True)

    class Meta:
        verbose_name = "User Workspace"
        verbose_name_plural = "User Workspaces"
        unique_together = ('user', 'api_name')

    @classmethod
    def get_or_create_for_user(cls, user, api_name='default'):
        if api_name not in settings.USER_OUTPUT_BASES:
            raise ValueError(f"Unknown API name:{api_name}")

        base_path = settings.USER_OUTPUT_BASES[api_name]
        obj, created = cls.objects.get_or_create(
            user=user,
            api_name=api_name,
            defaults={'directory': hash_user_dir(user.id)}
        )

        full_path = os.path.join(base_path, obj.directory)
        ensure_dir(full_path)
        if created:
            try:
                os.makedirs(full_path, exist_ok=True)

                assign_perm('view_userworkspace', user, obj)
                assign_perm('change_userworkspace', user, obj)
            except Exception as e:
                logger.error(f"Failed to create workspace directory {full_path}: {e}")

        return obj, full_path
