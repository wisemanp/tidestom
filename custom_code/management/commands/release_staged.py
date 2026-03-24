"""
Management command to release staged targets to public.

Usage:
    python manage.py release_staged

This command:
1. Updates staging area with any new observations
2. Promotes all staged targets to released
3. Logs the number of targets released

This should be run on a schedule (e.g., daily cron job or celery beat).
"""

from django.core.management.base import BaseCommand
from custom_code.services import update_staging_area, promote_staged_to_released


class Command(BaseCommand):
    help = 'Update staging area and release staged targets to public'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be released without actually releasing',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        # Update staging area with new observations
        self.stdout.write('Updating staging area...')
        newly_staged = update_staging_area()
        self.stdout.write(
            self.style.SUCCESS(f'  Added {newly_staged} new targets to staging area')
        )

        if dry_run:
            from custom_code.services import staged_queryset
            staged_count = staged_queryset().count()
            self.stdout.write(
                self.style.WARNING(
                    f'DRY RUN: Would release {staged_count} staged targets'
                )
            )
            return

        # Promote staged to released
        self.stdout.write('Promoting staged targets to released...')
        released_count = promote_staged_to_released()
        self.stdout.write(
            self.style.SUCCESS(f'  Released {released_count} targets to public')
        )

        self.stdout.write(self.style.SUCCESS('Release complete!'))
