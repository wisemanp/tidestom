from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
import hashlib
import os

def hash_user_dir(user_id: int):
    salt = getattr(settings, "USER_HASH_SALT", "fallback_salt")
    return hashlib.sha256(f"{user_id}{salt}".encode()).hexdigest()

class UserWorkspace(models.Model):
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE)
    directory = models.CharField(max_length=64, unique=True)

    class Meta:
        permissions = [
                #("view_userworkspace", "Can view this user's workspace"),
                ("change_userworkspace", "Can modify this user's workspace"),
            ]

    @property
    def patch(self):
        return os.path.join(settings.USER_OUTPUT_BASE, self.directory)

    @classmethod
    def get_or_create_for_user(cls, user):
        obj, created = cls.objects.get_or_create(
                user=user,
                defaults={'directory': hash_user_dir(user.id)}
            )
        os.makedirs(obj.path, exist_ok=True)
        return obj
