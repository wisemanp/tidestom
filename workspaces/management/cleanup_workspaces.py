from django.core.management.base import BaseCommand
from django.utils import timezone
from workspaces.models import UserWorkspace
from datetime import timedelta
import os

RETENTION_DAYS = 30

class Command(BaseCommand):
    help = "Clean up user workspaces older than 30 days"

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(days=RETENTION_DAYS)

        for workspace in UserWorkspace.objects.all():
            if not os.path.exists(workspace.path):
                continue

            for root, dirs, files in os.walk(workspace.path):
                for f in files:
                    fp = os.path.join(root, f)
                    try:
                        mtime = timezone.datetime.fromtimestamp(os.path.getmtime(fp),
                                                                tz=timezone.utc)
                        if mtime < cutoff:
                            os.remove(fp)
                            self.stdout.write(f"Deleted old file: {fp}")
                    except Exception as e:
                        self.stderr.write(f"Error deleting {fp}: {e}")

